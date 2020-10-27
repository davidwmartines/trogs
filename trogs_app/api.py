
import json

from flask import Flask, current_app, jsonify, request, session
from marshmallow import ValidationError, validate
from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Relationship, Schema
from werkzeug.exceptions import Forbidden, NotFound, UnprocessableEntity

import admin.albums
import admin.artists
import admin.files
import admin.names
import auth
import ids


class ArtistSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True)
    bio = fields.Str()
    profile_image_url = fields.Str(dump_only=True)
    thumbnail_image_url = fields.Str(dump_only=True)

    class Meta:
        type_ = "artist"


class AlbumSchema(Schema):
    id = fields.Str(dump_only=True)
    title = fields.Str(required=True)
    release_date = fields.Str(required=True)
    sort = fields.Int(dump_only=True)
    profile_image_url = fields.Str(dump_only=True)
    thumbnail_image_url = fields.Str(dump_only=True)

    class Meta:
        type_ = "album"
        

def J(*args, **kwargs):
    """Wrapper around jsonify that sets the Content-Type of the response to
    application/vnd.api+json.
    """
    response = jsonify(*args, **kwargs)
    response.mimetype = "application/vnd.api+json"
    return response


def current_user_email():
    return session['profile']['email']


def get_resized_image_url(path, dim, **kwargs):
    if not path:
        return ''

    return current_app.resize(path, dim, **kwargs)


@current_app.route('/api/v1/me/artists')
@auth.requires_auth
def my_artists():
    owner = current_user_email()
    artists = admin.artists.list_for_owner(owner)
    for artist in artists:
        try:
            artist.thumbnail_image_url = get_resized_image_url(
                artist.image_url, '50x50')
        except Exception as e:
            print(e)
    data = ArtistSchema(many=True).dump(artists)
    return data


@current_app.route('/api/v1/me/artists/<id>')
@auth.requires_auth
def my_artist_by_id(id):
    owner = current_user_email()
    artist = admin.artists.by_id_for_owner(id=id, owner=owner)
    if artist is None:
        raise NotFound

    artist.profile_image_url = get_resized_image_url(
        artist.image_url, '300')
    data = ArtistSchema().dump(artist)
    return data


@current_app.route('/api/v1/me/artists', methods=['POST'])
@auth.requires_auth
def add_my_artist():

    # load data and schema-validate
    schema = ArtistSchema()
    input_data = request.get_json() or {}
    try:
        data = schema.load(input_data)
    except ValidationError as err:
        return J(err.messages), 422

    # set owner
    data['owner'] = current_user_email()

    # save
    try:
        artist = admin.artists.create(data)
    except admin.artists.NameIsTaken as err:
        return J(to_error_object(err.message)), 422

    # return result
    data = schema.dump(artist)
    return J(data)


@current_app.route('/api/v1/me/artists/<artist_id>', methods=['PATCH'])
@auth.requires_auth
def edit_my_artist(artist_id):

    # load data and schema-validate
    schema = ArtistSchema()
    input_data = request.get_json() or {}
    try:
        data = schema.load(input_data)
    except ValidationError as err:
        return J(err.messages), 422

    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    # save
    try:
        artist = admin.artists.update(artist, data)
    except admin.artists.NameIsTaken as err:
        return J(to_error_object(err.message)), 422

    # return result
    artist.profile_image_url = get_resized_image_url(
        artist.image_url, '300')
    data = schema.dump(artist)
    return J(data)



@current_app.route('/api/v1/me/artists/<artist_id>/image', methods=['POST'])
@auth.requires_auth
def add_image(artist_id):

    # validate posted data
    if 'image_file' not in request.files:
        return J(to_error_object('no image_file posted')), 400

    # todo VERIFY jpeg

    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    # persist image
    file_data = request.files['image_file']
    object_name = 'art/{0}-{1}/{0}-{2}.jpg'.format(
        artist.normalized_name, artist.id, ids.new_id()[:8])
    admin.files.save(file_data, object_name, content_type='image/jpeg')
    if artist.image_url:
        admin.files.delete(artist.image_url)

    # update artist with new image_url
    admin.artists.update_image_url(artist_id, object_name)

    # return entity with new profile_url
    artist.profile_image_url = get_resized_image_url(
        object_name, '300')
    data = ArtistSchema().dump(artist)
    return J(data)


@current_app.route('/api/v1/me/artists/<artist_id>', methods=['DELETE'])
@auth.requires_auth
def delete_my_artist(artist_id):

    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    admin.artists.delete(artist)

    return '', 204


@current_app.route('/api/v1/me/artists/<artist_id>/albums')
@auth.requires_auth
def list_my_artist_albums(artist_id):

    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    albums = admin.albums.list_for_artist(artist_id)
    for album in albums:
        try:
            album.thumbnail_image_url = get_resized_image_url(
                album.image_url, '80x80')
        except Exception as e:
            print(e)
    data = AlbumSchema(many=True).dump(albums)
    return data


def to_error_object(message):
    """ make a JSONAPI error object from a single message string """
    return {'errors': [{'detail': message}]}
