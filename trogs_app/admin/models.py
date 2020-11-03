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


class Featured(Model):
    pass


import datetime, dateutil
def parse_release_date(item):
    date_string = item.get(
        'ReleaseDate', datetime.datetime.now().strftime('%Y-%m-%d'))
    return dateutil.parser.parse(date_string).strftime('%Y-%m-%d')
