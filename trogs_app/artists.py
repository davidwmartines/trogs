import dateutil.parser
from boto3.dynamodb.conditions import Key

import db, ids


@db.handle_db_error
def list_all():
    table = db.get_table()
    response = table.query(
        IndexName='GSI1',
        ScanIndexForward=True,
        KeyConditionExpression=Key('GSI1PK').eq('ARTISTS')
    )
    return map(map_list_item, response['Items'])


@db.handle_db_error
def get_by_id(id):
    pk = ids.from_id(id)
    table = db.get_table()
    response = table.query(
        IndexName='GSI2',
        ScanIndexForward=True,
        KeyConditionExpression=Key('GSI2PK').eq(pk)
    )
    if(len(response['Items']) == 0):
        return None
        
    detail = map_detail(response['Items'])
    return detail


def map_list_item(item):
    return {
        'name': item['GSI1SK'],
        'id': ids.to_id(item['PK']),
        'image_url': item.get('ImageURL')
    }


def map_detail(items):
    artist = items[0]
    children = items[slice(1, len(items)+1)]
    return {
        'artistId': artist['PK'],
        'name': artist['GSI1SK'],
        'image_url': artist.get('ImageURL'),
        'albums': list(map(map_album, filter(is_album, children))),
        'singles': list(map(map_single, filter(is_single, children)))
    }

def is_album(item):
    return 'GSI1PK' in item


def is_single(item):
    return not is_album(item)


def map_album(item):
    return {
        'title': item['AlbumTitle'],
        'year': dateutil.parser.parse(item['GSI2SK']).strftime('%Y'),
        'id': ids.to_id(item['SK']),
        'image_url': item.get('ImageURL')
    }

def map_single(item):
    return {
        'title': item['TrackTitle'],
        'year': dateutil.parser.parse(item['GSI2SK']).strftime('%Y'),
        'id': ids.to_id(item['SK'])
    }
