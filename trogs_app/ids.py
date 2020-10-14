from base64 import urlsafe_b64decode, urlsafe_b64encode


def to_id(key):
    return urlsafe_b64encode(key.encode()).decode()


def from_id(id):
    return urlsafe_b64decode(id.encode()).decode()
