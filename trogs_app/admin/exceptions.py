
class ModelException(Exception):
    message = "invalid data"

class InvalidData(ModelException):
    def __init__(self, message):
        self.message = message

class NameIsTaken(ModelException):
    message = 'Artist name is not available.'

class AlbumTitleExists(ModelException):
    message = 'Artist already has an album with that title.'

class TrackTitleExists(ModelException):
    message = "Album already has a track with that title."

class SingleTitleExists(ModelException):
    message = "Artist already has a single with that title."

class ExcessFeaturedAttempted(ModelException):
    def __init__(self, max_count):
        self.message = "Artist already has {0} tracks featured.  Remove one or more tracks from the featured list first.".format(max_count)