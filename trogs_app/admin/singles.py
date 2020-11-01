import datetime

import db
import ids
from boto3.dynamodb.conditions import Key

from . import exceptions, names
from .models import Artist, Single, parse_release_date


DEFAULT_LICENSE = 'by-nc-nd'


def item_to_single(item):
    return Single(
        id=item['PK'],
        title=item['TrackTitle'],
        audio_url=item['AudioURL'],
        license=item.get('License', ''),
        release_date=parse_release_date(item),
        sort=item['AC_SK'],
        featured=bool(item.get('Featured', False)),
        artist=Artist(id=item['AC_PK'], name=item.get('ArtistName'))
    )


def single_to_item(single):
    return {
        'PK': single.id,
        'SK': single.id,
        'TrackTitle': single.title,
        'AudioURL': single.audio_url,
        'AC_PK': single.artist.id,
        'AC_SK': single.sort,
        'ArtistID': single.artist.id,
        'ArtistName': single.artist.name,
        'License': single.license
    }


def list_for_artist(artist_id):
    table = db.get_table()
    res = table.query(
        IndexName='IX_ARTIST_CONTENT',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AC_PK').eq(
            artist_id) & Key('AC_SK').begins_with('3')
    )
    return list(map(item_to_single, res['Items']))


def create(artist, single_title, audio_url):
    existing_singles = list_for_artist(artist.id)
    if len(existing_singles) > 0:
        if any(ex.title == single_title for ex in existing_singles):
            dedupe_num = 0
            test_title = single_title
            while any(ex.title == test_title for ex in existing_singles):
                dedupe_num += 1
                test_title = single_title + ' ' + str(dedupe_num)
            single_title = test_title

        last = existing_singles[-1]
        last_sort = int(last.sort)
        sort = str(last_sort + 1)
    else:
        sort = '300'

    single = Single(
        id=ids.new_id(),
        title=single_title,
        audio_url=audio_url,
        sort=sort,
        artist=artist,
        license=DEFAULT_LICENSE,
        release_date=datetime.datetime.utcnow().strftime('%Y-%m-%d')
    )

    item = single_to_item(single)
    table = db.get_table()
    table.put_item(Item=item)

    return single


def get_by_id(single_id):
    table = db.get_table()

    res = table.query(
        KeyConditionExpression=Key('PK').eq(
            single_id) & Key('SK').eq(single_id)
    )

    if len(res['Items']) == 0:
        return None

    return item_to_single(res['Items'][0])


def update(single, data):
    for key, val in data.items():
        setattr(single, key, val)

    # check name
    existing_singles = list_for_artist(single.artist.id)
    if any((ex.title == single.title and ex.id != single.id) for ex in existing_singles):
        raise exceptions.SingleTitleExists

    table = db.get_table()
    table.update_item(
        Key={
            'PK': single.id,
            'SK': single.id
        },
        UpdateExpression='set TrackTitle = :title, ReleaseDate = :release_date, License = :license',
        ExpressionAttributeValues={
            ':title': single.title,
            ':release_date': single.release_date,
            ':license': single.license
        }
    )
    return single


def delete(single):
    table = db.get_table()
    table.delete_item(
        Key={'PK': single.id, 'SK': single.id}
    )

def sort(artist, single_id, direction):

    singles = list_for_artist(artist.id)

    if len(singles) < 2:
        raise exceptions.ModelException(
            message='too few singles to perform a sort')

    if direction not in ['up', 'down']:
        raise exceptions.InvalidData('invalid direction')

    # get index of track being moved
    track_index = next((i for i, t in enumerate(
        singles) if t.id == single_id), None)
    if track_index is None:
        raise exceptions.InvalidData("invaid single id")

    # determine track to "bump" (i.e. swap sorts with)
    if direction == 'up':
        if track_index == 0:
            track_to_bump = singles[-1]
        else:
            track_to_bump = singles[track_index-1]
    else:
        if track_index == len(singles)-1:
            track_to_bump = singles[0]
        else:
            track_to_bump = singles[track_index+1]

    # swap their sorts
    track_to_move = singles[track_index]
    current_sort = track_to_move.sort
    track_to_move.sort = track_to_bump.sort
    track_to_bump.sort = current_sort

    #print('move track {0} from {1} to {2}'.format(track_to_move.title, current_sort, track_to_move.sort))
    #print('bump track {0} to {1}'.format(track_to_bump.title, track_to_bump.sort))

    # persist changes to both tracks in transaction
    updates = [_make_sort_update(track_to_move),
               _make_sort_update(track_to_bump)]
    # print(updates)
    db.get_client().transact_write_items(TransactItems=updates)

    # re-sort list
    singles.sort(key=lambda i: i.sort)

    return singles



def _make_sort_update(single):
    """
    creates a TransactWriteItem for updating the sort of a single.
    """
    return {
        'Update': {
            'Key': {
                'PK': {'S': single.id},
                'SK': {'S': single.id}
            },
            'UpdateExpression': 'set AC_SK = :sort',
            'ExpressionAttributeValues': {':sort': {'S': single.sort}},
            'TableName': db.TABLE_NAME
        }
    }

