import os
import sys
import boto3
import re
from boto3.dynamodb.conditions import Key

bucket = os.environ["AWS_CONTENT_BUCKET"]

def save(file_data, object_name, content_type):

    print('saving file data', object_name)
    # upload
    client = boto3.client('s3')
    client.upload_fileobj(file_data, bucket, object_name, ExtraArgs={'ACL': 'public-read', 'ContentType': content_type})

    # show summary for verification
    resource = boto3.resource('s3')
    summary = resource.ObjectSummary(bucket, object_name)
    print(summary.size, summary.last_modified)

    # return full url to file
    location = client.get_bucket_location(Bucket=bucket)['LocationConstraint']
    url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, object_name)
    return url


def safe_obj_name(val):
    return re.sub(r'\W+', '', val.lower().replace(' ', '_').replace('-', '_')).replace("_", "-")
