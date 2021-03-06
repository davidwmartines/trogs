import datetime

import db
import ids
from boto3.dynamodb.conditions import Key

from . import names
from . import exceptions
from .models import Artist


def item_to_artist(item):
    """
    Converts a dictionary from the database to an Artist instance.
    """
    return Artist(
        id=item['PK'],
        name=item['AA_SK'],
        bio=item.get('Bio', ''),
        normalized_name=item.get('NormalizedName'),
        image_url=item.get('ImageURL'),
        profile_image_url='',
        thumbnail_image_url=''
    )


def artist_to_item(artist):
    """
    Converts an Artist instance to a dictionary for saving to the database.
    """
    return {
        'PK': artist.id,
        'SK': artist.id,
        'AA_SK': artist.name,
        'Owner': artist.owner,
        'AA_PK': 'ARTISTS',
        'AC_PK': artist.id,
        'AC_SK': '000',
        'Bio': artist.bio,
        'ImageURL': artist.image_url,
        'NormalizedName': artist.normalized_name,
        'CreatedDate': datetime.datetime.utcnow().isoformat(timespec='seconds')
    }


def list_for_owner(owner):
    """
    Gets a list of artists for the specified owner.
    """

    table = db.get_table()

    res = table.query(
        IndexName='IX_ARTISTS_BY_OWNER',
        KeyConditionExpression=Key('Owner').eq(owner)
    )

    return list(map(item_to_artist, res['Items']))


def by_id_for_owner(id, owner):
    """
    Gets an Artist instnace by id, only for the specified owner str.
    """

    table = db.get_table()

    res = table.query(
        IndexName='IX_ARTISTS_BY_OWNER',
        KeyConditionExpression=Key('Owner').eq(owner)
        & Key('PK').eq(id)
    )

    if not len(res['Items']):
        return None

    return item_to_artist(res['Items'][0])


def create(data):
    """
    Creates a new artist from the supplied data, and saves to database.

    Parameters
    ----------
    data: dict
        Dictionary of attribute values.

    Returns
    -------
        The new Artist instance.
    """

    artist = Artist(id=ids.new_id(), **data)
    artist.normalized_name = names.safe_obj_name(artist.name)
    artist.image_url = ''

    if name_is_taken(artist.normalized_name):
        raise exceptions.NameIsTaken

    item = artist_to_item(artist)
    table = db.get_table()
    table.put_item(Item=item)
    return artist


def update(artist, data):
    """
    Updates attributes of the artist from the supplied data.

    Parameters
    ----------
    artist: Artist
        The Artist instance to update.
    data: dict
        Dictionary of attribute values.

    Returns
    -------
        The modified Artist instance.
    """
    print('updating artist', artist.id)

    # if neither of these attributes changed, just return
    if data['name'] == artist.name and data["bio"] == artist.bio:
        return artist

    if data['name'] == artist.name:
        # just update bio
        table = db.get_table()

        table.update_item(
            Key={
                'PK': artist.id,
                'SK': artist.id
            },
            UpdateExpression='set Bio = :bio',
            ExpressionAttributeValues={
                ':bio': data["bio"]
            }
        )
        artist.bio = data['bio']
        return artist
    else:
        raise Exception("can't change artist names yet.")


def update_image_url(artist_id, image_url):
    print('updating image url', artist_id, image_url)
    table = db.get_table()
    table.update_item(
        Key={
            'PK': artist_id,
            'SK': artist_id
        },
        UpdateExpression='set ImageURL = :image_url',
        ExpressionAttributeValues={
            ':image_url': image_url
        }
    )
    print('done')


def delete(artist):
    print('deleting artist', artist.id)

    # get list of existing content
    table = db.get_table()
    content = table.query(
        IndexName='IX_ARTIST_CONTENT',
        ScanIndexForward=True,
        KeyConditionExpression=Key('AC_PK').eq(artist.id)
    )

    # content response items includes one row for artist.
    if len(content['Items']) == 1:
        # no albums or singles... ok to just delete artist record.
        table.delete_item(
            Key={'PK': artist.id, 'SK': artist.id}
        )
    else:
        # delete artist plus all content in transaction(s)

        # content = artist, albums, singles
        items_to_delete = content['Items']

        # album tracks
        for item in list(filter(lambda i: (i['AC_SK'].startswith('2')), content['Items'])):
            album_content = table.query(
                IndexName="IX_ARTISTS_ALBUMS",
                ScanIndexForward=True,
                KeyConditionExpression=Key('AA_PK').eq(item['AA_PK'])
            )
            #album content = album item plus track items
            if len(album_content['Items']) > 1:
                tracks = album_content['Items'][1:]
                # get tracks from album not already in list to delete (if they were from the featured artist content)
                non_featured_tracks = list(filter(lambda t: (not any(t['PK'] == d['PK'] for d in items_to_delete)), tracks))
                items_to_delete.extend(non_featured_tracks)

        db.transactionally_delete(items_to_delete)


def name_is_taken(test_name, exclude_id=None):
    """
    Used to determine if an artist name is already used.

    Parameters
    ----------
    test_name : str 
        the name to check

    exclude_id : str
        optional, used in edit scenarios to not check the current owner

    Returns
    -------
        boolean, if true name is already taken and artist should not be persisted with this name.

    """

    table = db.get_table()
    result = table.query(
        IndexName='IX_ARTISTS_NAMES',
        KeyConditionExpression=Key('NormalizedName').eq(test_name)
    )

    if len(result['Items']) == 0:
        return False

    if exclude_id is None:
        return True

    return len(filter(lambda item: item['PK'] != exclude_id, result['Items'])) != 0


