import os
from base64 import urlsafe_b64decode, urlsafe_b64encode

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

ERROR_HELP_STRINGS = {
    # Common Errors
    'InternalServerError': 'Internal Server Error, generally safe to retry with exponential back-off',
    'ProvisionedThroughputExceededException': 'Request rate is too high. If you\'re using a custom retry strategy make sure to retry with exponential back-off.' +
                                              'Otherwise consider reducing frequency of requests or increasing provisioned capacity for your table or secondary index',
    'ResourceNotFoundException': 'One of the tables was not found, verify table exists before retrying',
    'ServiceUnavailable': 'Had trouble reaching DynamoDB. generally safe to retry with exponential back-off',
    'ThrottlingException': 'Request denied due to throttling, generally safe to retry with exponential back-off',
    'UnrecognizedClientException': 'The request signature is incorrect most likely due to an invalid AWS access key ID or secret key, fix before retrying',
    'ValidationException': 'The input fails to satisfy the constraints specified by DynamoDB, fix input before retrying',
    'RequestLimitExceeded': 'Throughput exceeds the current throughput limit for your account, increase account level throughput before retrying',
}

def get_table():
    endpoint_url = os.environ["AWS_ENDPOINT_URL"]
    if (endpoint_url != ''):
        dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    else:
        dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("art")
    return table

def handle_error(error):
    error_code = error.response['Error']['Code']
    error_message = error.response['Error']['Message']

    error_help_string = ERROR_HELP_STRINGS[error_code]

    print('[{error_code}] {help_string}. Error message: {error_message}'
          .format(error_code=error_code,
                  help_string=error_help_string,
                  error_message=error_message))

def map_list_item(item):
    return {
        'name': item['name'],
        'id': urlsafe_b64encode(item['PK'].encode())
        }

def list_all():
    table = get_table()
    try:
        response = table.query(
            IndexName='IX_ARTIST',
            ScanIndexForward=True,
            KeyConditionExpression=Key('TYPE').eq('ARTIST')
        )
        #print(response)
        return map(map_list_item, response['Items'])

    except ClientError as error:
        handle_error(error)

    except BaseException as error:
        print("Unknown error while querying: " + error)

def map_detail(items):

    artist = {
        'name': items[0]['name'],
        'albums' : map(map_album, items[slice(1, len(items)+1)])
    }

    return artist

def map_album(item):
    return {
        'title': item['title'],
        'year': item['SK'],
        'id': urlsafe_b64encode(item['SK'].encode())
    }


def get_by_id(id):
    print(id)
    pk = urlsafe_b64decode(id.encode()).decode()

    table = get_table()
    try:
        response = table.query(
            ScanIndexForward=True,
            KeyConditionExpression=Key('PK').eq(pk)
        )
        print(response)
        detail =  map_detail(response['Items'])
        print(detail)
        return detail

    except ClientError as error:
        handle_error(error)

    except BaseException as error:
        print(error)
