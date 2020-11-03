from . import progress
import os, sys
import boto3
from boto3.dynamodb.conditions import Key

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

from trogs_app import db
from trogs_app.admin import names

def add_artist_normalized_names():

    table = db.get_table()

    response = table.query(
        IndexName='IX_ARTISTS_ALBUMS',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AA_PK').eq('ARTISTS'),
        ProjectionExpression='PK, SK, AA_SK, NormalizedName'
    ) 

    for item in response['Items']:

        normalized_name = item.get('NormalizedName')
        if normalized_name :
            print('"{0}" already has "{1}"'.format(item['AA_SK'], normalized_name))
        else:
            normalized_name = names.safe_obj_name(item['AA_SK'])
            print('setting "{0}" to "{1}"'.format( item['AA_SK'], normalized_name))
            table.update_item(
                Key={
                    'PK': item['PK'],
                    'SK': item['SK']
                },
                UpdateExpression='set NormalizedName = :normalized_name',
                ExpressionAttributeValues={
                    ':normalized_name': normalized_name
                },
                ReturnValues='UPDATED_NEW'
            )
        #print(res)