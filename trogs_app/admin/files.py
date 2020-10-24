import os
import sys
import boto3
from boto3.dynamodb.conditions import Key


bucket = os.environ["AWS_CONTENT_BUCKET"]


def save(file_data, object_name, content_type):

    print('saving file data', object_name)
    # upload
    client = _get_client()
    client.upload_fileobj(file_data, bucket, object_name, ExtraArgs={'ACL': 'public-read', 'ContentType': content_type})

    # show summary for verification
    resource = _get_resource()
    summary = resource.ObjectSummary(bucket, object_name)
    print('success', summary.size, summary.last_modified)

    # return full url to file
    location = client.get_bucket_location(Bucket=bucket)['LocationConstraint']
    url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, object_name)
    return url


def _get_client():
    if 'AWS_CONTENT_REGION' not in os.environ:
        # use current profile for all AWS params (should the default usage in production)
        return boto3.client('s3')
    else:
        # use override values from env (for development to override profile)
        return boto3.client('s3',
            region_name=os.environ['AWS_CONTENT_REGION'],
            aws_access_key_id=os.environ['AWS_CONTENT_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_CONTENT_SECRET_ACCESS_KEY']
        )

def _get_resource():
    if 'AWS_CONTENT_REGION' not in os.environ:
        # use current profile for all AWS params (should the default usage in production)
        return boto3.resource('s3')
    else:
        # use override values from env (for development to override profile)
        return boto3.resource('s3',
            region_name=os.environ['AWS_CONTENT_REGION'],
            aws_access_key_id=os.environ['AWS_CONTENT_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_CONTENT_SECRET_ACCESS_KEY']
        )
