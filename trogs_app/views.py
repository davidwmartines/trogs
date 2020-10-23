
from flask import Flask, render_template, current_app
from werkzeug.exceptions import NotFound

import albums
import artists
import tracks
import auth

@current_app.route('/')
def home():
    allArtists = artists.list_all()
    return render_template("home.html", artists=allArtists)


@current_app.route('/artist/<id>')
def artist(id):
    artist = artists.get_by_id(id)
    if artist is None:
        raise NotFound
    return render_template("artist.html", artist=artist)


@current_app.route('/album/<id>')
def album(id):
    album = albums.get_by_id(id)
    if album is None:
        raise NotFound
    return render_template("album.html", album=album)


@current_app.route('/track/<id>')
def track(id):
    track = tracks.get_by_id(id)
    if track is None:
        raise NotFound
    return render_template("track.html", track=track)


@current_app.route('/create')
@auth.requires_auth
def create():
    return render_template('admin_home.html')
