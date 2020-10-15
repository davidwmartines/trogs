import dateutil.parser
from boto3.dynamodb.conditions import Key

from . import db, ids


@db.handle_db_error
def get_by_id(id):
    albumId = ids.from_id(id)
    table = db.get_table()
    response = table.query(
        IndexName="IX_ALBUM",
        ScanIndexForward=True,
        KeyConditionExpression=Key('AlbumID').eq(albumId)
    )
    if(len(response['Items']) < 1):
        return None
    return map_album(response['Items'])


def map_album(items):
    return {
        'albumId': items[0]['AlbumID'],
        'title': items[0]['AlbumTitle'],
        'artistName': items[0]['ArtistName'],
        'year': dateutil.parser.parse(items[0]['SK']).strftime('%Y'),
        'artistId': ids.to_id(items[0]['ArtistID']),
        'tracks': list(map(map_track, items[slice(1, len(items)+1)]))
    }


def map_track(item):
    return {
        'trackId': ids.to_id(item['PK']),
        'title': item['TrackTitle'],
        'audioUrl': item['AudioURL']
    }
