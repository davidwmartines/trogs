import datetime

import db
import ids
from boto3.dynamodb.conditions import Key

from . import names
from .models import Album

def item_to_album(item):
    """
    Converts a dictionary from the database to an Album instance.
    """
    return Album(
        id=item['AA_PK'],
        title=item['AlbumTitle'],
        description=item.get('Description', ''),
        license = item.get('License', ''),
        image_url=item.get('ImageURL'),
        sort = item['AC_SK'],
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

    table = db.get_table()
    # get next sort order
    res = table.query(
        IndexName='IX_ARTIST_CONTENT',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AC_PK').eq(
            artist.id) & Key('AC_SK').begins_with('2')
    )
    existing_albums = list(map(item_to_album, res['Items']))
    if len(existing_albums) > 0:
        last_album = existing_albums[-1]
        last_sort = int(last_album.sort)
        album.sort = str(last_sort + 1)
    else:
        album.sort = '200'

    print("creating '{0}', id '{1}', sort {2}".format(album.title, album.id, album.sort))

    table.put_item(Item=album_to_item(album))
    return album

