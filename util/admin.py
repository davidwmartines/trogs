from .import progress
from trogs_app import db, ids
import os
import sys
import boto3
from boto3.dynamodb.conditions import Key

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


def create_artist(artistName, owner='', bio='', imageUrl=''):
    table = db.get_table()

    id = ids.new_id()

    print("creating '{0}', id '{1}'".format(artistName, id))

    table.put_item(Item={
        'PK': id,
        'SK': '000',
        'ArtistName': artistName,
        'Owner': owner,
        'IsArtist': 1,
        'Bio': bio,
        'ImageURL': imageUrl
    })

    query = table.query(
        IndexName="IX_ARTIST",
        KeyConditionExpression=Key('IsArtist').eq(
            1) & Key('ArtistName').eq(artistName)
    )

    print(query["Items"][0])


def create_album(artistName, albumTitle, releaseDateISO, license, description='', imageUrl=''):
    table = db.get_table()

    res = table.query(
        IndexName='IX_ARTIST',
        KeyConditionExpression=Key('IsArtist').eq(
            1) & Key('ArtistName').eq(artistName)
    )

    if(len(res['Items']) == 0):
        print("Error: No artist found named '{0}'.".format(artistName))
        return

    artist = res['Items'][0]
    print(artist)

    id = ids.new_id()

    print("creating '{0}', id '{1}'".format(albumTitle, id))

    table.put_item(Item={
        'PK': artist['PK'],
        'SK': releaseDateISO,
        'AlbumTitle': albumTitle,
        'AlbumID': id,
        'ArtistID': artist['PK'],
        'ArtistName': artist['ArtistName'],
        'Description': description,
        'License': license,
        'ImageURL': imageUrl
    })

    query = table.query(
        IndexName="IX_ALBUM",
        KeyConditionExpression=Key('AlbumID').eq(id)
    )

    print(query["Items"][0])


def add_track(artistName, albumTitle, trackTitle, audioUrl, sortNum=None):
    table = db.get_table()

    res = table.query(
        IndexName='IX_ARTIST',
        KeyConditionExpression=Key('IsArtist').eq(
            1) & Key('ArtistName').eq(artistName)
    )

    if(len(res['Items']) == 0):
        print("Error: No artist found named '{0}'.".format(artistName))
        return

    artist = res['Items'][0]

    print(artist)

    res = table.query(
        ScanIndexForward=True,
        KeyConditionExpression=Key('PK').eq(artist['PK'])
    )

    albums = list(filter(lambda item: attr_matches(
        'AlbumTitle', albumTitle, item), res['Items']))

    if(len(albums) == 0):
        print("Error: No album found by '{0}' with title '{1}'.".format(
            artist["ArtistName"], albumTitle))
        return

    album = albums[0]

    print(album)

    if(sortNum is None):
        res = table.query(
            IndexName='IX_ALBUM',
            ScanIndexForward=True,
            KeyConditionExpression=Key('AlbumID').eq(album['AlbumID'])
        )

        if(len(res['Items']) > 1):
            lastTrack = res['Items'][len(res['Items'])-1]
            lastSortNum = int(lastTrack['SK'].split('TRACK-')[1])
            sort = 'TRACK-' + str(lastSortNum + 100)
        else:
            sort = 'TRACK-100'
    else:
        sort = 'TRACK-' + str(sortNum)

    id = ids.new_id()

    print("creating '{0}', id '{1}', sort {2}".format(trackTitle, id, sort))

    table.put_item(Item={
        'PK': id,
        'SK': sort,
        'TrackTitle': trackTitle,
        'AudioURL': audioUrl,
        'AlbumTitle': albumTitle,
        'AlbumID': album['AlbumID'],
        'ArtistID': album['ArtistID'],
        'ArtistName': album['ArtistName']
    })

    res = table.query(
        KeyConditionExpression=Key('PK').eq(id)
    )

    print(res["Items"][0])


def attr_matches(attr, value, item):
    if(attr in item):
        return item[attr] == value


def save_to_s3(local_file_path, object_name, content_type, bucket=None):

    # get bucket from param or config
    if(bucket is None):
        if(os.environ["AWS_CONTENT_BUCKET"] is not None):
            bucket = os.environ["AWS_CONTENT_BUCKET"]
    if(bucket is None):
        raise "No S3 bucket specified"

    # upload
    client = boto3.client('s3')
    with open(local_file_path, 'rb') as f:
        client.upload_fileobj(f, bucket, object_name,
                              ExtraArgs={'ACL': 'public-read',
                                         'ContentType': content_type},
                              Callback=progress.UploadProgressCallback(local_file_path))

    # show summary for verification
    resource = boto3.resource('s3')
    summary = resource.ObjectSummary(bucket, object_name)
    print(summary.size, summary.last_modified)

    # return full url to file
    location = client.get_bucket_location(Bucket=bucket)['LocationConstraint']
    url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, object_name)
    return url


def safe_obj_name(val):
    return val.lower().replace(' ', '-').replace('/', '-').replace('\\', '-').replace('#', '-')
