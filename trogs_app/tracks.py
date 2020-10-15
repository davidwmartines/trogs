from boto3.dynamodb.conditions import Key

from . import db

@db.handle_db_error
def get_by_id(id):
    table = db.get_table()

    res = table.query(
        KeyConditionExpression=Key('PK').eq(id)
    )

    if(len(res['Items']) == 0):
        return None

    item = res['Items'][0]

    return {
        'trackId': item['PK'],
        'artistId': item['ArtistID'],
        'artistName': item['ArtistName'],
        'albumId': item['AlbumID'],
        'albumTitle': item['AlbumTitle'],
        'trackTitle': item['TrackTitle'],
        'audioUrl': item['AudioURL']
    }
