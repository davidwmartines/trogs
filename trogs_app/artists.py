import dateutil.parser
from boto3.dynamodb.conditions import Key

import db, ids, licenses


@db.handle_db_error
def list_all():
    table = db.get_table()
    response = table.query(
        IndexName='IX_ARTISTS_ALBUMS',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AA_PK').eq('ARTISTS'),
        ProjectionExpression='PK, AA_SK, ImageURL'
    )
    return map(map_list_item, response['Items'])


@db.handle_db_error
def get_by_id(id):
    pk = ids.from_id(id)
    table = db.get_table()
    response = table.query(
        IndexName='IX_ARTIST_CONTENT',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AC_PK').eq(pk)
    )
    if len(response['Items']) == 0:
        return None

    detail = map_detail(response['Items'])
    return detail


def map_list_item(item):
    return {
        'name': item['AA_SK'],
        'id': ids.to_id(item['PK']),
        'image_url': item.get('ImageURL')
    }


def map_detail(items):
    artist = items[0]
    children = items[slice(1, len(items)+1)]
    artist_detail = {
        'artistId': artist['AC_PK'],
        'name': artist['AA_SK'],
        'image_url': artist.get('ImageURL'),
        'featured_tracks': list(map(map_track, filter(is_featured, children))),
        'albums': list(map(map_album, filter(is_album, children))),
        'singles': list(map(map_track, filter(not_featured, filter(is_single, children))))
    }
    return artist_detail


def is_album(item):
    return not is_track(item)


def is_track(item):
    return 'TrackTitle' in item


def is_featured(item):
    return is_track(item) and item.get('Featured', False) == True


def not_featured(item):
    return not is_featured(item)


def is_single(item):
    return is_track(item) and 'AlbumTitle' not in item


def map_album(item):
    return {
        'title': item['AlbumTitle'],
        'year': dateutil.parser.parse(item['ReleaseDate']).strftime('%Y'),
        'id': ids.to_id(item['AA_PK']),
        'image_url': item.get('ImageURL')
    }


def map_track(item):
    track = {
        'title': item['TrackTitle'],
        'id': ids.to_id(item['PK']),
        'audio_url': item["AudioURL"]
    }
    if is_single(item):
        release_date = item['ReleaseDate']
        track['year'] = dateutil.parser.parse(release_date).strftime('%Y')
    if not is_single(item):
        track['album_title'] = item['AlbumTitle']
        track['album_id'] = item['AA_PK']
    
    license = item.get('License')
    if license:
        track["license"] = license
        track["license_name"] = licenses.names[license]

    return track

