from flask import Flask, render_template
from werkzeug.exceptions import NotFound

from . import albums, app, artists, tracks


@app.route("/")
def home():
    allArtists = artists.list_all()
    return render_template("home.html", artists=allArtists)


@app.route("/artist/<id>")
def artist(id):
    artist = artists.get_by_id(id)
    if(artist is None):
        raise NotFound
    return render_template("artist.html", artist=artist)


@app.route("/album/<id>")
def album(id):
    album = albums.get_by_id(id)
    if(album is None):
        raise NotFound
    return render_template("album.html", album=album)


@app.route("/track/<id>")
def track(id):
    track = tracks.get_by_id(id)
    if(track is None):
        raise NotFound
    return render_template("track.html", track=track)

@app.route("/favicon.ico")
def favicon():
    return app.send_static_file('favicon.ico')
