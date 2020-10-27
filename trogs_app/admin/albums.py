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
