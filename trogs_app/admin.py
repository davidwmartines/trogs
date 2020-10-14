from boto3.dynamodb.conditions import Key

from . import db, ids


def create_artist(artistName):
    table = db.get_table()

    id = ids.new_id()

    print("creating '{0}', id '{1}'".format(artistName, id))

    table.put_item(Item={
        'PK': id,
        'SK': '000',
        'ArtistName': artistName,
        'IsArtist': 1
    })

    query = table.query(
        IndexName="IX_ARTIST",
        KeyConditionExpression=Key('IsArtist').eq(
            1) & Key('ArtistName').eq(artistName)
    )

    print(query["Items"][0])


def create_album(artistName, albumTitle, releaseDateISO):
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
        'ArtistName': artist['ArtistName']
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
        ScanIndexForward = True,
        KeyConditionExpression=Key('PK').eq(artist['PK'])
    )

    albums = list(filter(lambda item: attr_matches('AlbumTitle', albumTitle, item), res['Items']))

    if(len(albums) == 0):
        print("Error: No album found by '{0}' with title '{1}'.".format(artist["ArtistName"], albumTitle))
        return

    album = albums[0]

    print(album)

    if(sortNum is None):
        res = table.query(
            IndexName = 'IX_ALBUM',
            ScanIndexForward = True,
            KeyConditionExpression = Key('AlbumID').eq(album['AlbumID'])
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

# class Artist:
#     def __init__(self, id, name):
#         self.id = id
#         self.name = name

#     def save(self):
#         table = db.get_table()
#         table.put_item(Item={
#             'PK': self.id,
#             'SK': '000',
#             'ArtistId': self.id,
#             'ArtistName': self.name,
#             'IsArtist': 1
#         })

#     def add_album(self, id, title, date):
#         table = db.get_table()
#         table.put_item(Item={
#             'PK': self.id,
#             'SK': date,
#             'AlbumTitle': title,
#             'AlbumID': id,
#             'ArtistID': self.id,
#             'ArtistName': self.name
#         })
