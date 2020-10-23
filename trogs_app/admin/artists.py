import ids, db
from boto3.dynamodb.conditions import Key

class Model:
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


class Artist(Model):
    pass

def item_to_artist(item):
    return Artist(
        id = item['PK'],
        name = item['AA_SK'],
        bio = item.get('Bio', ''),
        image_url = item.get('ImageURL', '')
    )

def list_for_owner(owner):

    table = db.get_table()

    res = table.query(
        IndexName="IX_ARTISTS_BY_OWNER",
        KeyConditionExpression=Key('Owner').eq(owner)
    )

    return list(map(item_to_artist, res['Items']))


def by_id_for_owner(id, owner):

    table = db.get_table()

    res = table.query(
        IndexName="IX_ARTISTS_BY_OWNER",
        KeyConditionExpression=Key('Owner').eq(owner)
        & Key('PK').eq(id)
    )

    if not len(res['Items']):
        return None

    return item_to_artist(res['Items'][0])

