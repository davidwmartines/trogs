from boto3.dynamodb.conditions import Key

import db

@db.handle_db_error
def get_by_id(id):
    table = db.get_table()

    res = table.query(
        KeyConditionExpression=Key('PK').eq(id) & Key('SK').eq(id)
    )

    if(len(res['Items']) == 0):
        return None

    item = res['Items'][0]

    track= {
        'id': item['PK'],
        'artist_id': item['AC_PK'],
        'artist_name': item['ArtistName'],
        'track_title': item['TrackTitle'],
        'audio_url': item['AudioURL']
    }
    album_id =  item.get('AA_PK', None)
    album_title = item.get('AlbumTitle', None)
    if(album_id is not None and album_title is not None):
        track['album_id'] = album_id
        track['album_title'] = album_title

    return track
