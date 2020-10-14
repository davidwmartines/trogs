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
    return map_album(response['Items'])


def map_album(items):
    return {
        'title': items[0]['AlbumTitle'],
        'artistName': items[0]['ArtistName'],
        'year': items[0]['Year'],
        'artistId': ids.to_id(items[0]['ArtistID']),
        'tracks': map(map_track, items[slice(1, len(items)+1)])
    }


def map_track(item):
    return {
        'id': ids.to_id(item['PK']),
        'title': item['TrackTitle'],
        'url': item['TrackURL']
    }
