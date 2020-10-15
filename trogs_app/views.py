
from flask import Flask, render_template
from werkzeug.exceptions import NotFound

import albums, artists, tracks


def home():
    allArtists = artists.list_all()
    return render_template("home.html", artists=allArtists)


def artist(id):
    artist = artists.get_by_id(id)
    if(artist is None):
        raise NotFound
    return render_template("artist.html", artist=artist)


def album(id):
    album = albums.get_by_id(id)
    if(album is None):
        raise NotFound
    return render_template("album.html", album=album)


def track(id):
    track = tracks.get_by_id(id)
    if(track is None):
        raise NotFound
    return render_template("track.html", track=track)


