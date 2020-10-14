#from base64 import urlsafe_b64decode, urlsafe_b64encode

import shortuuid

# preserved in case need to translate ids from dynamodb to url-safe values
def to_id(key):
    # return urlsafe_b64encode(key.encode()).decode()
    return key


def from_id(id):
    # return urlsafe_b64decode(id.encode()).decode()
    return id


def new_id():
    shortuuid.set_alphabet('1234567890abcdefghijklmnopqrstuvwxyz')
    return shortuuid.uuid()[:16]
