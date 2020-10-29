import datetime

import db
import ids
from boto3.dynamodb.conditions import Key

from . import names
from .models import Album, Artist

def item_to_album(item):
    """
    Converts a dictionary from the database to an Album instance.
    """
    return Album(
        id=item['AA_PK'],
        title=item['AlbumTitle'],
        description=item.get('Description', ''),
        license = item.get('License', ''),
        release_date = item.get('ReleaseDate'),
        image_url=item.get('ImageURL'),
        sort = item['AC_SK'],
        artist = Artist(id = item['PK'], name=item.get('ArtistName')),
        profile_image_url='',
        thumbnail_image_url=''
    )

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
        KeyConditionExpression=Key('AC_PK').eq(artist_id) & Key('AC_SK').begins_with('2')
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
        raise TitleExists

    if len(existing_albums) > 0:
        last_album = existing_albums[-1]
        last_sort = int(last_album.sort)
        album.sort = str(last_sort + 1)
    else:
        album.sort = '200'

    print("creating '{0}', id '{1}', sort {2}".format(album.title, album.id, album.sort))

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
    
    return item_to_album(res['Items'][0])


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
        raise TitleExists

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


class TitleExists(Exception):
    message = 'Artist already has an album with that title.'
