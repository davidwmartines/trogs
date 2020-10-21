from . import progress
from trogs_app import db, ids
import os
import sys
import boto3
import re
from boto3.dynamodb.conditions import Key

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

#
# ArtistContent sort key (AC_SK):
#   000  : the artist itself
#   100+ : featured tracks
#   200+ : albums
#   300+ : singles
#


def create_artist(artistName, owner='', bio='', imageUrl=''):
    table = db.get_table()

    id = ids.new_id()

    print("creating '{0}', id '{1}'".format(artistName, id))

    table.put_item(Item={
        'PK': id,
        'SK': id,
        'AA_SK': artistName,
        'Owner': owner,
        'AA_PK': 'ARTISTS',
        'AC_PK': id,
        'AC_SK': '000',
        'Bio': bio,
        'ImageURL': imageUrl
    })

    query = table.query(
        IndexName="IX_ARTISTS_ALBUMS",
        KeyConditionExpression=Key('AA_PK').eq(
            'ARTISTS') & Key('AA_SK').eq(artistName)
    )

    print(query["Items"][0])

    return id


def create_album(artistName, albumTitle, releaseDateISO, license, description='', imageUrl='', ac_sort=None):
    table = db.get_table()

    res = table.query(
        IndexName='IX_ARTISTS_ALBUMS',
        KeyConditionExpression=Key('AA_PK').eq(
            'ARTISTS') & Key('AA_SK').eq(artistName)
    )

    if len(res['Items']) == 0:
        print("Error: No artist found named '{0}'.".format(artistName))
        return

    artist = res['Items'][0]
    print(artist)

    id = ids.new_id()

    if ac_sort is None:
        res = table.query(
            IndexName='IX_ARTIST_CONTENT',
            ScanIndexForward=True,
            KeyConditionExpression=Key('AC_PK').eq(
                artist['PK']) & Key('AC_SK').begins_with('2')
        )

        if len(res['Items']) > 0:
            last_item = res['Items'][len(res['Items'])-1]
            last_sort = int(last_item['AC_SK'])
            ac_sort = str(last_sort + 1)
        else:
            ac_sort = '200'

    print("creating '{0}', id '{1}', sort {2}".format(albumTitle, id, ac_sort))

    table.put_item(Item={
        'PK': artist['PK'],
        'AA_PK': id,
        'AA_SK': '000',
        'AC_PK': artist['PK'],
        'AC_SK': ac_sort,
        'ReleaseDate': releaseDateISO,
        'AlbumTitle': albumTitle,
        'SK': id,
        'PK': artist['PK'],
        'ArtistName': artist['AA_SK'],
        'Description': description,
        'License': license,
        'ImageURL': imageUrl
    })

    query = table.query(
        IndexName="IX_ARTISTS_ALBUMS",
        KeyConditionExpression=Key('AA_PK').eq(id)
    )

    print(query["Items"][0])

    return id


def add_track(artistName, albumTitle, trackTitle, audioUrl, sortNum=None):
    table = db.get_table()

    res = table.query(
        IndexName='IX_ARTISTS_ALBUMS',
        KeyConditionExpression=Key('AA_PK').eq(
            'ARTISTS') & Key('AA_SK').eq(artistName)
    )

    if len(res['Items']) == 0:
        print("Error: No artist found named '{0}'.".format(artistName))
        return

    artist = res['Items'][0]

    print(artist)

    res = table.query(
        IndexName='IX_ARTIST_CONTENT',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AC_PK').eq(
            artist['PK']) & Key('AC_SK').begins_with('2')
    )

    albums = list(filter(lambda item: attr_matches(
        'AlbumTitle', albumTitle, item), res['Items']))

    if len(albums) == 0:
        print("Error: No album found by '{0}' with title '{1}'.".format(
            artist["ArtistName"], albumTitle))
        return

    album = albums[0]

    print(album)

    if sortNum is None:
        res = table.query(
            IndexName='IX_ARTISTS_ALBUMS',
            ScanIndexForward=True,
            KeyConditionExpression=Key('AA_PK').eq(
                album['AA_PK']) & Key('AA_SK').begins_with('1')
        )

        if len(res['Items']) > 0:
            last_track = res['Items'][len(res['Items'])-1]
            last_sort = int(last_track['AA_SK'])
            sort = str(last_sort + 1)
        else:
            sort = '100'
    else:
        sort = str(sortNum)

    id = ids.new_id()

    print("creating '{0}', id '{1}', sort {2}".format(trackTitle, id, sort))

    table.put_item(Item={
        'PK': id,
        'SK': id,
        'AA_PK': album['AA_PK'],
        'AA_SK': sort,
        'TrackTitle': trackTitle,
        'AudioURL': audioUrl,
        'AlbumTitle': albumTitle,
        'AlbumID': album['AA_PK'],
        'ArtistID': album['PK'],
        'ArtistName': album['ArtistName'],
        'License': album['License']
    })

    res = table.query(
        KeyConditionExpression=Key('PK').eq(id)
    )

    print(res["Items"][0])

    return id


def add_single(artistName, trackTitle, audioUrl, releaseDataISO, license, sortNum=None):
    table = db.get_table()

    res = table.query(
        IndexName='IX_ARTISTS_ALBUMS',
        KeyConditionExpression=Key('AA_PK').eq(
            'ARTISTS') & Key('AA_SK').eq(artistName)
    )

    if len(res['Items']) == 0:
        print("Error: No artist found named '{0}'.".format(artistName))
        return

    artist = res['Items'][0]

    print(artist)

    if sortNum is None:
        res = table.query(
            IndexName='IX_ARTIST_CONTENT',
            ScanIndexForward=True,
            KeyConditionExpression=Key('AC_PK').eq(
                artist['PK']) & Key('AC_SK').begins_with('3')
        )
        if len(res['Items']) > 0:
            last_track = res['Items'][len(res['Items'])-1]
            last_sort = int(last_track['AC_SK'])
            sort = str(last_sort + 1)
        else:
            sort = '300'
    else:
        sort = str(sortNum)

    id = ids.new_id()

    print("creating '{0}', id '{1}', sort {2}".format(trackTitle, id, sort))

    table.put_item(Item={
        'PK': id,
        'SK': id,
        'AC_PK': artist['PK'],
        'AC_SK': sort,
        'TrackTitle': trackTitle,
        'AudioURL': audioUrl,
        'ArtistID': artist['PK'],
        'ArtistName': artist['AA_SK'],
        'License': license,
        'ReleaseDate': releaseDataISO
    })

    res = table.query(
        KeyConditionExpression=Key('PK').eq(id)
    )

    print(res["Items"][0])

    return id


def feature_track(id):

    table = db.get_table()

    # get track
    res = table.query(
        KeyConditionExpression=Key('PK').eq(id) & Key('SK').eq(id)
    )
    if len(res['Items']) == 0:
        print('no track found by id', id)
        return
    track = res['Items'][0]

    # determine feature sort
    sort = '100'
    res = table.query(
        IndexName='IX_ARTIST_CONTENT',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AC_PK').eq(
            track['ArtistID']) & Key('AC_SK').begins_with('1')
    )
    if len(res['Items']) > 0:
        last_track = res['Items'][len(res['Items'])-1]
        last_sort = int(last_track['AC_SK'])
        sort = str(last_sort + 1)


    # define update
    update_exp = 'set AC_PK = :AC_PK, AC_SK = :AC_SK, Featured= :Featured'
    update_exp_vals = {
            ':AC_PK': track['ArtistID'],
            ':AC_SK': sort,
            ':Featured': True
        }

    # update
    res = table.update_item(
        Key={
            'PK': id,
            'SK': id
        },
        UpdateExpression=update_exp,
        ExpressionAttributeValues=update_exp_vals,
        ReturnValues='UPDATED_NEW'
    )

    print(res)


def unfeature_track(id):

    table = db.get_table()

     # get track
    res = table.query(
        KeyConditionExpression=Key('PK').eq(id) & Key('SK').eq(id)
    )
    if len(res['Items']) == 0:
        print('no track found by id', id)
        return
    track = res['Items'][0]

    # define update
    key = {
            'PK': id,
            'SK': id
        }
    update_exp = 'remove Featured'
    update_exp_vals = None

    # if album track, ok to remove from AC
    if 'AlbumID' in track:
        update_exp + ', AC_SK, AC_PK'
    else:
        # determine sort for single
        sort = '300'
        res = table.query(
            IndexName='IX_ARTIST_CONTENT',
            ScanIndexForward=True,
            KeyConditionExpression=Key('AC_PK').eq(
                track['ArtistID']) & Key('AC_SK').begins_with('3')
        )
        if len(res['Items']) > 0:
            last_track = res['Items'][len(res['Items'])-1]
            last_sort = int(last_track['AC_SK'])
            sort = str(last_sort + 1)
        update_exp += ' set AC_SK = :AC_SK'
        update_exp_vals = {':AC_SK': sort}

    # update
    
    if update_exp_vals:
        res = table.update_item(
            Key=key,
            UpdateExpression=update_exp,
            ExpressionAttributeValues=update_exp_vals,
            ReturnValues='UPDATED_NEW'
        )
    else:
        res = table.update_item(
            Key=key,
            UpdateExpression=update_exp,
            ReturnValues='UPDATED_NEW'
        )

    print(res)


def delete_track(id):
    table = db.get_table()

    key = {
        'PK': id,
        'SK': id
    }
    
    res = table.delete_item(
        Key = key
    )

    print(res)


def attr_matches(attr, value, item):
    if attr in item:
        return item[attr] == value


def save_to_s3(local_file_path, object_name, content_type, bucket=None):

    # get bucket from param or config
    if bucket is None:
        if "AWS_CONTENT_BUCKET" in os.environ:
            bucket = os.environ["AWS_CONTENT_BUCKET"]
    if bucket is None:
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
    return re.sub(r'\W+', '', val.lower().replace(' ', '_').replace('-', '_')).replace("_", "-")
