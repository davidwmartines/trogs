import dateutil.parser
from boto3.dynamodb.conditions import Key

from . import db, ids


@db.handle_db_error
def list_all():
    table = db.get_table()
    response = table.query(
        IndexName='IX_ARTIST',
        ScanIndexForward=True,
        KeyConditionExpression=Key('IsArtist').eq(1)
    )
    return map(map_list_item, response['Items'])


@db.handle_db_error
def get_by_id(id):
    pk = ids.from_id(id)
    table = db.get_table()
    response = table.query(
        ScanIndexForward=True,
        KeyConditionExpression=Key('PK').eq(pk)
    )
    if(len(response['Items']) == 0):
        return None
        
    detail = map_detail(response['Items'])
    return detail


def map_list_item(item):
    return {
        'name': item['ArtistName'],
        'id': ids.to_id(item['PK'])
    }


def map_detail(items):
    return {
        'name': items[0]['ArtistName'],
        'albums': map(map_album, items[slice(1, len(items)+1)])
    }


def map_album(item):
    return {
        'title': item['AlbumTitle'],
        'year': dateutil.parser.parse(item['SK']).strftime('%Y'),
        'id': ids.to_id(item['AlbumID'])
    }
