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


def add_feature_sort():

    table = db.get_table()
    # for each artist
    response = table.query(
        IndexName='IX_ARTISTS_ALBUMS',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AA_PK').eq('ARTISTS'),
        ProjectionExpression='PK, AA_SK'
    )

    for item in response['Items']:
        artist_id = item['PK']
        print('checking artist {0}'.format(item['AA_SK']))
        # get featured tracks
        content = table.query(
            IndexName='IX_ARTIST_CONTENT',
            ScanIndexForward=True,
            KeyConditionExpression=Key('AC_PK').eq(artist_id)
        )
        featured = list(filter(lambda i: bool(i.get('Featured', False)), content['Items']))
        print('found {0} featured tracks'.format(len(featured)))
        for track_item in featured:
            if not 'FeatureSort' in track_item:
                print('adding feature sort to {0}'.format(track_item['TrackTitle']))
                #set FeatureSort = existing AC_SK
                feature_sort = track_item['AC_SK']
                content_sort = None
                if not 'AA_PK' in track_item:
                    print('setting single back to proper AC_SK')
                    res = table.query(
                            IndexName='IX_ARTIST_CONTENT',
                            ScanIndexForward=True,
                            KeyConditionExpression=Key('AC_PK').eq(
                                artist_id) & Key('AC_SK').begins_with('3')
                        )
                    content_sort = '300'
                    if len(res['Items']) > 0:
                        last = res['Items'][-1]
                        last_sort = int(last['AC_SK'])
                        content_sort = str(last_sort + 1)

            print('setting featuresort to {0} and content_sort to {1}'.format(feature_sort, content_sort))
            update_exp = 'set FeatureSort = :feature_sort'
            update_exp_vals = {
                ':feature_sort': feature_sort
            }
            if content_sort is not None:
                update_exp += ', AC_SK = :content_sort'
                update_exp_vals[':content_sort'] = content_sort
           
            table.update_item(
                Key = {'PK': track_item['PK'], 'SK': track_item['SK']},
                UpdateExpression = update_exp,
                ExpressionAttributeValues = update_exp_vals
            )

