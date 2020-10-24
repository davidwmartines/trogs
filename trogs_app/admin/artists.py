import ids
import db
from boto3.dynamodb.conditions import Key


class Model:
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


class Artist(Model):
    pass


def item_to_artist(item):
    """
    Converts a dictionary from the database to an Artist instance.
    """
    return Artist(
        id=item['PK'],
        name=item['AA_SK'],
        bio=item.get('Bio', ''),
        image_url=item.get('ImageURL', '')
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
        'ImageURL': artist.image_url
    }


def list_for_owner(owner):
    """
    Gets a list of artists for the specified owner.
    """

    table = db.get_table()

    res = table.query(
        IndexName="IX_ARTISTS_BY_OWNER",
        KeyConditionExpression=Key('Owner').eq(owner)
    )

    return list(map(item_to_artist, res['Items']))


def by_id_for_owner(id, owner):
    """
    Gets an Artist instnace by id, only for the specified owner str.
    """

    table = db.get_table()

    res = table.query(
        IndexName="IX_ARTISTS_BY_OWNER",
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
    id = ids.new_id()
    artist = Artist(id=id, **data)

    if name_is_taken(artist.name):
        raise NameIsTaken

    item = artist_to_item(artist)
    table = db.get_table()
    table.put_item(Item=item)
    return artist


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

    # This approach does NOT account for casing variations.  
    # Need to use separate index with RANGE key on a normalized version of the name, i.e. all lowercased.
    table = db.get_table()
    result = table.query(
        IndexName="IX_ARTISTS_ALBUMS",
        KeyConditionExpression=Key('AA_PK').eq(
            'ARTISTS') & Key('AA_SK').eq(test_name))

    if len(result['Items']) == 0:
        return False

    if exclude_id is None:
        return True

    return len(filter(lambda item: item['PK'] != exclude_id, result['Items'])) != 0


class NameIsTaken(Exception):
    message ="Artist name is not available."
    
