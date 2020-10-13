import os
from base64 import urlsafe_b64decode, urlsafe_b64encode
from boto3.dynamodb.conditions import Key

from . import db


@db.handle_db_error
def list_all():
    table = db.get_table()
    response = table.query(
        IndexName='IX_ARTIST',
        ScanIndexForward=True,
        KeyConditionExpression=Key('TYPE').eq('ARTIST')
    )
    # print(response)
    return map(map_list_item, response['Items'])


@db.handle_db_error
def get_by_id(id):
    # print(id)
    pk = urlsafe_b64decode(id.encode()).decode()

    table = db.get_table()

    response = table.query(
        ScanIndexForward=True,
        KeyConditionExpression=Key('PK').eq(pk)
    )
    # print(response)
    detail = map_detail(response['Items'])
    # print(detail)
    return detail


def map_list_item(item):
    return {
        'name': item['name'],
        'id': urlsafe_b64encode(item['PK'].encode())
    }


def map_detail(items):
    return {
        'name': items[0]['name'],
        'albums': map(map_album, items[slice(1, len(items)+1)])
    }


def map_album(item):
    return {
        'title': item['title'],
        'year': item['SK'],
        'id': urlsafe_b64encode(item['SK'].encode())
    }
