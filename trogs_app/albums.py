from base64 import urlsafe_b64decode, urlsafe_b64encode
from boto3.dynamodb.conditions import Key

from . import db

@db.handle_db_error
def get_by_id(id):
    print(id)
    albumId = urlsafe_b64decode(id.encode()).decode()
    print(albumId)
    table = db.get_table()

    response = table.query(
        IndexName="IX_ALBUM",
        ScanIndexForward=True,
        KeyConditionExpression=Key('AlbumID').eq(albumId)
    )
    print(response)

    return map_album(response['Items'])

def map_album(items):
    return {
        'title': items[0]['title'],
        'tracks': map(map_track, items[slice(1, len(items)+1)])
    }

def map_track(item):
    return {
        'id': item['PK'],
        'title': item['title']
    }