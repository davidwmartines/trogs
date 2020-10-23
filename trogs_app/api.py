
from flask import Flask, current_app, jsonify, session
from werkzeug.exceptions import NotFound, Forbidden, UnprocessableEntity

import admin.artists

import auth

def current_user_email():
    return session['profile']['email']


@current_app.route('/api/v1/me/artists')
@auth.requires_auth
def my_artists():

    owner = current_user_email()

    artists = admin.artists.list_for_owner(owner)
    
    return jsonify({
        'data': artists
    })


@current_app.route('/api/v1/me/artists/<id>')
@auth.requires_auth
def my_artist_by_id(id):
    artist = {
        'id': id,
        'attributes': {
            'name': id
        }
    }
    return jsonify({
        'data': artist
    })

