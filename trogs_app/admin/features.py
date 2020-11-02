import db
from boto3.dynamodb.conditions import Key
from .models import Album, Featured
from . import exceptions


# The total number of featured tracks/singles allowed per artist.
MAX_FEATURES = 3


def item_to_featured(item):
    featured = Featured(
        id=item['PK'],
        title=item['TrackTitle'],
        audio_url=item['AudioURL'],
        sort=item['AC_SK'],
        album=None
    )

    album_id = item.get('AA_PK')
    if album_id:
        featured.album = Album(id=album_id, title=item['AlbumTitle'])

    return featured


def list_for_artist(artist_id):
    table = db.get_table()
    response = table.query(
        IndexName='IX_ARTIST_CONTENT',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AC_PK').eq(
            artist_id) & Key('AC_SK').begins_with('1')
    )
    if len(response['Items']) == 0:
        return None

    return list(map(item_to_featured, response['Items']))


def feature_item(artist_id, item_id):
    table = db.get_table()

    # get track
    res = table.query(
        KeyConditionExpression=Key('PK').eq(item_id) & Key('SK').eq(item_id)
    )
    if len(res['Items']) == 0:
        raise exceptions.InvalidData('invalid item id')
    track = res['Items'][0]

    if track['ArtistID'] != artist_id:
        raise exceptions.InvalidData('track not in artist')

    # validate feature count and determine feature sort
    res = table.query(
        IndexName='IX_ARTIST_CONTENT',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AC_PK').eq(
            artist_id) & Key('AC_SK').begins_with('1')
    )
    if len(res['Items']) >= MAX_FEATURES:
        raise exceptions.ExcessFeaturedAttempted(MAX_FEATURES)

    sort = '100'
    if len(res['Items']) > 0:
        last_track = res['Items'][-1]
        last_sort = int(last_track['AC_SK'])
        sort = str(last_sort + 1)

    # define update
    update_exp = 'set AC_PK = :AC_PK, AC_SK = :AC_SK, Featured = :Featured'
    update_exp_vals = {
        # adding item to artist content and sorting:
        ':AC_PK': artist_id,
        ':AC_SK': sort,
        # set featured flag true
        ':Featured': True
    }

    # update
    res = table.update_item(
        Key={
            'PK': item_id,
            'SK': item_id
        },
        UpdateExpression=update_exp,
        ExpressionAttributeValues=update_exp_vals
    )


def unfeature_item(artist_id, item_id):
    table = db.get_table()

    # get track
    res = table.query(
        KeyConditionExpression=Key('PK').eq(item_id) & Key('SK').eq(item_id)
    )
    if len(res['Items']) == 0:
        raise exceptions.InvalidData('invalid item id')
    track = res['Items'][0]

    if track['ArtistID'] != artist_id:
        raise exceptions.InvalidData('track not in artist')

    # define update
    key = {
        'PK': item_id,
        'SK': item_id
    }
    update_exp = 'remove Featured'
    update_exp_vals = None

    # if album track, ok to remove from AC
    if 'AA_PK' in track:
        update_exp += ', AC_SK, AC_PK'
    else:
        # if single, need to add back to singles list with sort
        sort = '300'
        res = table.query(
            IndexName='IX_ARTIST_CONTENT',
            ScanIndexForward=True,
            KeyConditionExpression=Key('AC_PK').eq(
                artist_id) & Key('AC_SK').begins_with('3')
        )
        if len(res['Items']) > 0:
            last_track = res['Items'][-1]
            last_sort = int(last_track['AC_SK'])
            sort = str(last_sort + 1)
        update_exp += ' set AC_SK = :AC_SK'
        update_exp_vals = {':AC_SK': sort}

    # update
    print('update_exp', update_exp)

    if update_exp_vals:
        res = table.update_item(
            Key=key,
            UpdateExpression=update_exp,
            ExpressionAttributeValues=update_exp_vals
        )
    else:
        res = table.update_item(
            Key=key,
            UpdateExpression=update_exp
        )


def sort_featured(artist, item_id, direction):
    items = list_for_artist(artist.id)

    if len(items) < 2:
        raise exceptions.InvalidData(
            message='too few featured to perform a sort')

    if direction not in ['up', 'down']:
        raise exceptions.InvalidData('invalid direction')

    # get index of track being moved
    track_index = next((i for i, t in enumerate(
        items) if t.id == item_id), None)
    if track_index is None:
        raise exceptions.InvalidData("invaid item id")

    # determine track to "bump" (i.e. swap sorts with)
    if direction == 'up':
        if track_index == 0:
            track_to_bump = items[-1]
        else:
            track_to_bump = items[track_index-1]
    else:
        if track_index == len(items)-1:
            track_to_bump = items[0]
        else:
            track_to_bump = items[track_index+1]

    # swap their sorts
    track_to_move = items[track_index]
    current_sort = track_to_move.sort
    track_to_move.sort = track_to_bump.sort
    track_to_bump.sort = current_sort

    # persist changes to both tracks in transaction
    updates = [_make_sort_update(track_to_move),
               _make_sort_update(track_to_bump)]
    # print(updates)
    db.get_client().transact_write_items(TransactItems=updates)

    # re-sort list
    items.sort(key=lambda i: i.sort)

    return items


def _make_sort_update(featured_item):
    """
    creates a TransactWriteItem for updating the sort of featured item.
    """
    return {
        'Update': {
            'Key': {
                'PK': {'S': featured_item.id},
                'SK': {'S': featured_item.id}
            },
            'UpdateExpression': 'set AC_SK = :sort',
            'ExpressionAttributeValues': {':sort': {'S': featured_item.sort}},
            'TableName': db.TABLE_NAME
        }
    }
