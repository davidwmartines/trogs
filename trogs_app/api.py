
from flask import Flask, current_app, jsonify, session
from marshmallow import ValidationError, validate
from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Relationship, Schema
from werkzeug.exceptions import Forbidden, NotFound, UnprocessableEntity

import admin.artists
import auth


class ArtistSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)
    owner = fields.Str(required=True)
    image_url = fields.Str()
    bio = fields.Str()

    class Meta:
        type_ = "artist"


def J(*args, **kwargs):
    """Wrapper around jsonify that sets the Content-Type of the response to
    application/vnd.api+json.
    """
    response = jsonify(*args, **kwargs)
    response.mimetype = "application/vnd.api+json"
    return response


def current_user_email():
    return session['profile']['email']


@current_app.route('/api/v1/me/artists')
@auth.requires_auth
def my_artists():
    owner = current_user_email()
    artists = admin.artists.list_for_owner(owner)
    data = ArtistSchema(many=True).dump(artists)
    return data


@current_app.route('/api/v1/me/artists/<id>')
@auth.requires_auth
def my_artist_by_id(id):
    owner = current_user_email()
    artist = admin.artists.by_id_for_owner(id=id, owner=owner)
    print('artist', artist)
    if artist is None:
        raise NotFound

    data = ArtistSchema().dump(artist)
    return data

