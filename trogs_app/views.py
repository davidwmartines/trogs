from flask import Flask, render_template

from . import albums, app, artists, tracks


@app.route("/")
def home():
    allArtists = artists.list_all()
    return render_template("home.html", artists=allArtists)


@app.route("/artist/<id>")
def artist(id):
    artist = artists.get_by_id(id)
    return render_template("artist.html", artist=artist)


@app.route("/album/<id>")
def album(id):
    album = albums.get_by_id(id)
    return render_template("album.html", album=album)


@app.route("/track/<id>")
def track(id):
    track = tracks.get_by_id(id)
    return render_template("track.html", track=track)
