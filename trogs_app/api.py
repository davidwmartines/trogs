
import json

from flask import Flask, current_app, jsonify, request, session
from marshmallow import ValidationError, validate
from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Relationship, Schema
from werkzeug.exceptions import Forbidden, NotFound, UnprocessableEntity

import admin.artists
import admin.files
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
    if artist is None:
        raise NotFound

    data = ArtistSchema().dump(artist)
    return data


@current_app.route('/api/v1/me/artists', methods=['POST'])
@auth.requires_auth
def add_my_artist():
    schema = ArtistSchema()

    input_data = json.loads(request.form['data']) or {}
    input_data["data"]["attributes"]["owner"] = current_user_email()

    # id should be dump_only, so if client sends it, ignore it
    del input_data["data"]["id"]

    # do not take image_url as input... must be set server-side based on uploaded file
    input_data["data"]["attributes"]["image_url"] = ""

    if 'image_file' in request.files:
        safe_name = admin.file_save.safe_obj_name(
            input_data["data"]["attributes"]["name"])
        file_data = request.files['image_file']
        object_name = 'art/{0}/{0}.jpg'.format(safe_name)
        admin.files.save(file_data, object_name, content_type='image/jpeg')
        input_data["attributes"]["image_url"] = object_name

    print("input_data", input_data)

    try:
        data = schema.load(input_data)
    except ValidationError as err:
        return J(err.messages), 422

    artist = admin.artists.create(data)

    data = schema.dump(artist)
    return J(data)
