import datetime

import db
import ids
from boto3.dynamodb.conditions import Key

from . import names
from . import exceptions
from .models import Artist, Single, parse_release_date


def item_to_single(item):
    return Single(
        id=item['PK'],
        title=item['TrackTitle'],
        audio_url=item['AudioURL'],
        license=item.get('License', ''),
        release_date=parse_release_date(item),
        sort=item['AC_SK'],
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