from boto3.dynamodb.conditions import Key
import dateutil
import db, licenses

@db.handle_db_error
def get_by_id(id):
    table = db.get_table()

    res = table.query(
        KeyConditionExpression=Key('PK').eq(id) & Key('SK').eq(id)
    )

    if len(res['Items']) == 0:
        return None

    item = res['Items'][0]

    track= {
        'id': item['PK'],
        'artist_id': item['ArtistID'],
        'artist_name': item['ArtistName'],
        'track_title': item['TrackTitle'],
        'audio_url': item['AudioURL']
    }
    album_id =  item.get('AA_PK')
    album_title = item.get('AlbumTitle')
    if album_id and album_title:
        track['album_id'] = album_id
        track['album_title'] = album_title

    license = item.get('License')
    if license:
        track["license"] = license
        track["license_name"] = licenses.names[license]
    
    release_date = item.get('ReleaseDate')
    if release_date:
        track['year'] = dateutil.parser.parse(release_date).strftime('%Y')

    return track
