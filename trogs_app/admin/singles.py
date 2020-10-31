import datetime

import db
import ids
from boto3.dynamodb.conditions import Key

from . import names
from . import exceptions
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


def get_by_id(single_id):
    pass


def update(single, data):
    pass


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
