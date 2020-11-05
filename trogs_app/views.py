
import datetime

from flask import (Flask, current_app, make_response, redirect,
                   render_template, request, session, url_for)
from werkzeug.exceptions import NotFound

import albums
import artists
import auth
import tracks


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
    if not session.get('agree_to_terms') and not request.cookies.get('agree_to_terms'):
        return render_template("agreement.html")
    
    return render_template('admin_home.html', env=current_app.env)


@current_app.route('/create', methods=["POST"])
@auth.requires_auth
def agree_to_terms():  

    session['agree_to_terms'] = True

    expire_date = datetime.datetime.now()
    expire_date = expire_date + datetime.timedelta(days=90)
    response = make_response(redirect(url_for('create')))
    response.set_cookie('agree_to_terms', '1', expires=expire_date)
    return response


@current_app.route("/health")
def heath_check():
    return "ok", 200

