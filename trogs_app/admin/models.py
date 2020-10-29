class Model:
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


class Album(Model):
    pass


class Track(Model):
    pass


class Single(Model):
    pass


class Artist(Model):
    pass
