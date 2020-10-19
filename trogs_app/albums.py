import dateutil.parser
from boto3.dynamodb.conditions import Key

import db, ids


@db.handle_db_error
def get_by_id(id):
    albumId = ids.from_id(id)
    table = db.get_table()
    response = table.query(
        IndexName="IX_ARTISTS_ALBUMS",
        ScanIndexForward=True,
        KeyConditionExpression=Key('AA_PK').eq(albumId)
    )
    if(len(response['Items']) < 1):
        return None
    return map_album(response['Items'])


def map_album(items):
    album = items[0]
    return {
        'id': album['AA_PK'],
        'title': album['AlbumTitle'],
        'artist_name': album['ArtistName'],
        'year': dateutil.parser.parse(album['ReleaseDate']).strftime('%Y'),
        'artist_id': ids.to_id(album['PK']),
        'image_url': album.get('ImageURL'),
        'tracks': list(map(map_track, items[slice(1, len(items)+1)]))
    }


def map_track(item):
    return {
        'id': ids.to_id(item['PK']),
        'title': item['TrackTitle'],
        'audio_url': item['AudioURL']
    }
