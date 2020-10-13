import os

import boto3
from botocore.exceptions import ClientError


def get_table():
    endpoint_url = os.environ["AWS_ENDPOINT_URL"]
    if (endpoint_url != ''):
        dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    else:
        dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("art")
    return table


def handle_db_error(wrapped_function):
    def _wrapper(*args, **kwargs):
        try:
            response = wrapped_function(*args, **kwargs)
        except ClientError as error:
            handle_client_error(error)
        except BaseException as error:
            print(error)
        return response
    return _wrapper


def handle_client_error(error):
    error_code = error.response['Error']['Code']
    error_message = error.response['Error']['Message']

    error_help_string = ERROR_HELP_STRINGS[error_code]

    print('[{error_code}] {help_string}. Error message: {error_message}'
          .format(error_code=error_code,
                  help_string=error_help_string,
                  error_message=error_message))


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
