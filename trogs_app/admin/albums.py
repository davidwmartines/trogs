import datetime

import dateutil.parser
import db
import ids
from boto3.dynamodb.conditions import Key

from . import exceptions, names
from .models import Album, Artist, Track, parse_release_date


def item_to_album(item):
    """
    Converts a dictionary from the database to an Album instance.
    """
    return Album(
        id=item['AA_PK'],
        title=item['AlbumTitle'],
        description=item.get('Description', ''),
        license=item.get('License', ''),
        release_date=parse_release_date(item),
        image_url=item.get('ImageURL'),
        sort=item['AC_SK'],
        artist=Artist(id=item['PK'], name=item.get('ArtistName')),
        profile_image_url='',
        thumbnail_image_url='',
        tracks=[]
    )


def item_to_track(item):
    """
    Converts a dictionary from the database to an album Track instance.
    """
    return Track(
        id=item['PK'],
        title=item['TrackTitle'],
        audio_url=item['AudioURL'],
        sort=item['AA_SK']
    )


def track_to_item(track):
    return {
        'PK': track.id,
        'SK': track.id,
        'AA_PK': track.album.id,
        'AA_SK': track.sort,
        'TrackTitle': track.title,
        'AudioURL': track.audio_url,
        'AlbumTitle': track.album.title,
        'AlbumID': track.album.id,
        'ArtistID': track.album.artist.id,
        'ArtistName': track.album.artist.name,
        'License': track.album.license
    }


def album_to_item(album):
    """
    converts an album into a database item to persist.
    """
    return {
        'PK': album.artist.id,
        'AA_PK': album.id,
        'AA_SK': '000',
        'AC_PK': album.artist.id,
        'AC_SK': album.sort,
        'ReleaseDate': album.release_date,
        'AlbumTitle': album.title,
        'SK': album.id,
        'PK': album.artist.id,
        'ArtistName': album.artist.name,
        'Description': album.description,
        'License': album.license,
        'ImageURL': album.image_url
    }


def list_for_artist(artist_id):
    """
    Gets a list of albums for the artist
    """

    table = db.get_table()

    res = table.query(
        IndexName='IX_ARTIST_CONTENT',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AC_PK').eq(
            artist_id) & Key('AC_SK').begins_with('2')
    )

    return list(map(item_to_album, res['Items']))


def add(artist, data):
    """
    Adds an album to the artist.
    """

    album = Album(id=ids.new_id(), artist=artist, image_url='', **data)
    if not hasattr(album, 'license'):
        setattr(album, 'license', '')
    if not hasattr(album, 'description'):
        setattr(album, 'description', '')

    table = db.get_table()
    # get existing albums to check name and get next sort
    res = table.query(
        IndexName='IX_ARTIST_CONTENT',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AC_PK').eq(
            artist.id) & Key('AC_SK').begins_with('2'),
        ProjectionExpression='PK, AA_PK, AC_SK, AlbumTitle'
    )
    existing_albums = list(map(item_to_album, res['Items']))
    if any(album.title == existing.title for existing in existing_albums):
        raise exceptions.AlbumTitleExists

    if len(existing_albums) > 0:
        last_album = existing_albums[-1]
        last_sort = int(last_album.sort)
        album.sort = str(last_sort + 1)
    else:
        album.sort = '200'

    print("creating '{0}', id '{1}', sort {2}".format(
        album.title, album.id, album.sort))

    table.put_item(Item=album_to_item(album))
    return album


def get_by_id(album_id):
    table = db.get_table()

    res = table.query(
        IndexName='IX_ARTISTS_ALBUMS',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AA_PK').eq(album_id)
    )

    if not res['Items']:
        return None
    items = res['Items']

    album = item_to_album(items[0])
    album.tracks = list(map(item_to_track, items[slice(1, len(items)+1)]))
    return album


def update_image_url(artist_id, album_id, image_url):
    print('updating album image url', album_id, image_url)
    table = db.get_table()
    table.update_item(
        Key={
            'PK': artist_id,
            'SK': album_id
        },
        UpdateExpression='set ImageURL = :image_url',
        ExpressionAttributeValues={
            ':image_url': image_url
        }
    )
    print('done')


def update(album, data):

    for key, val in data.items():
        setattr(album, key, val)

    # get existing albums to check name
    table = db.get_table()
    res = table.query(
        IndexName='IX_ARTIST_CONTENT',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AC_PK').eq(
            album.artist.id) & Key('AC_SK').begins_with('2'),
        ProjectionExpression='PK, AA_PK, AC_SK, AlbumTitle'
    )
    existing_albums = list(map(item_to_album, res['Items']))
    if any((album.title == existing.title and album.id != existing.id) for existing in existing_albums):
        raise exceptions.AlbumTitleExists

    table.update_item(
        Key={
            'PK': album.artist.id,
            'SK': album.id
        },
        UpdateExpression='set AlbumTitle = :title, ReleaseDate = :release_date, License = :license, Description = :description',
        ExpressionAttributeValues={
            ':title': album.title,
            ':release_date': album.release_date,
            ':license': album.license,
            ':description': album.description
        }
    )
    return album


def create_track(album, track_title, audio_url):

    if len(album.tracks) > 0:

        if any(existing_track.title == track_title for existing_track in album.tracks):
            raise exceptions.TrackTitleExists

        last_track = album.tracks[-1]
        last_sort = int(last_track.sort)
        sort = str(last_sort + 1)
    else:
        sort = '100'

    track = Track(
        id=ids.new_id(),
        title=track_title,
        audio_url=audio_url,
        sort=sort,
        album=album)

    item = track_to_item(track)
    table = db.get_table()
    table.put_item(Item=item)

    return track


def sort_track(album, track_id, direction):

    if len(album.tracks) < 2:
        raise exceptions.ModelException(
            message='too few tracks to perform a sort')

    if direction not in ['up', 'down']:
        raise exceptions.InvalidData('invalid direction')

    # get index of track being moved
    track_index = next((i for i, t in enumerate(
        album.tracks) if t.id == track_id), None)
    if track_index is None:
        raise exceptions.InvalidData("invaid track id")

    # determine track to "bump" (i.e. swap sorts with)
    if direction == 'up':
        if track_index == 0:
            track_to_bump = album.tracks[-1]
        else:
            track_to_bump = album.tracks[track_index-1]
    else:
        if track_index == len(album.tracks)-1:
            track_to_bump = album.tracks[0]
        else:
            track_to_bump = album.tracks[track_index+1]

    # swap their sorts
    track_to_move = album.tracks[track_index]
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
    album.tracks.sort(key=lambda i: i.sort)


def _make_sort_update(track):
    """
    creates a TransactWriteItem for updating the sort of a track.
    """
    return {
        'Update': {
            'Key': {
                'PK': {'S': track.id},
                'SK': {'S': track.id}
            },
            'UpdateExpression': 'set AA_SK = :sort',
            'ExpressionAttributeValues': {':sort': {'S': track.sort}},
            'TableName': db.TABLE_NAME
        }
    }


def change_track_title(album, track_id, new_title):
    # get track to rename
    track = next((t for t in album.tracks if t.id == track_id), None)
    if track is None:
        raise exceptions.InvalidData("invaid track")

    # check unique name
    if any((existing_track.title == new_title and existing_track.id != track.id) for existing_track in album.tracks):
        raise exceptions.TrackTitleExists

    track.title = new_title

    table = db.get_table()
    table.update_item(
        Key={
            'PK': track.id,
            'SK': track.id
        },
        UpdateExpression='set TrackTitle = :new_title',
        ExpressionAttributeValues={
            ':new_title': track.title
        }
    )
    return track


def delete_album(album):
    table = db.get_table()
    if len(album.tracks) == 0:
        table.delete_item(
            Key={'PK': album.artist.id, 'SK': album.id}
        )
    else:
        items_to_delete = []
        items_to_delete.append({'PK': album.artist.id, 'SK': album.id})
        items_to_delete.extend(
            map(lambda track: ({'PK': track.id, 'SK': track.id}), album.tracks))
        db.transactionally_delete(items_to_delete)


def delete_track(album, track_id):
    index = next((i for i, t in enumerate(
        album.tracks) if t.id == track_id), None)
    if index is None:
        raise exceptions.InvalidData("invaid track")

    track = album.tracks[index]
    album.tracks.remove(track)

    table = db.get_table()
    table.delete_item(
        Key={
            'PK': track.id,
            'SK': track.id
        }
    )

    return album
