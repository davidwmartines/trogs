
import json
import os.path
from flask import Flask, current_app, jsonify, request, session
from marshmallow import ValidationError, validate
from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Relationship, Schema
from werkzeug.exceptions import Forbidden, NotFound, UnprocessableEntity

import admin.albums
import admin.artists
import admin.files
import admin.names
import admin.exceptions
import admin.singles
import admin.sanitize
import auth
import ids


class ArtistSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, error='Name cannot be blank'))
    bio = fields.Str()
    profile_image_url = fields.Str(dump_only=True)
    thumbnail_image_url = fields.Str(dump_only=True)

    class Meta:
        type_ = "artist"


class TrackSchema(Schema):
    id = fields.Str(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, error='Title cannot be blank'))
    audio_url = fields.Str(dump_only=True)
    sort= fields.Str(dump_only=True)

    class Meta:
        type_ = "track"


class AlbumSchema(Schema):
    id = fields.Str(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, error='Title cannot be blank'))
    release_date = fields.Str(required=True)
    license = fields.Str(default='')
    description = fields.Str(default='')
    sort = fields.Int(dump_only=True)
    profile_image_url = fields.Str(dump_only=True)
    thumbnail_image_url = fields.Str(dump_only=True)

    tracks = fields.List(fields.Nested(TrackSchema), dump_only=True)

    class Meta:
        type_ = "album"


class SingleSchema(Schema):
    id = fields.Str(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, error='Title cannot be blank'))
    release_date = fields.Str(required=True)
    license = fields.Str(default='')
    audio_url = fields.Str(dump_only=True)
    sort= fields.Str(dump_only=True)

    class Meta:
        type_ = "single"



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

    try:
        return current_app.resize(path, dim, **kwargs)
    except Exception as e:
        print(e)
        return ''


@current_app.route('/api/v1/me/artists')
@auth.requires_auth
def my_artists():
    owner = current_user_email()
    artists = admin.artists.list_for_owner(owner)
    for artist in artists:
        artist.thumbnail_image_url = get_resized_image_url(
            artist.image_url, '50x50')

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
        admin.sanitize.trim_strings(data)
    except ValidationError as err:
        return J(err.messages), 422

    # set owner
    data['owner'] = current_user_email()

    # save
    try:
        artist = admin.artists.create(data)
    except admin.exceptions.ModelException as err:
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
        admin.sanitize.trim_strings(data)
    except ValidationError as err:
        return J(err.messages), 422

    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    # save
    try:
        artist = admin.artists.update(artist, data)
    except admin.exceptions.ModelException as err:
        return J(to_error_object(err.message)), 422

    # return result
    artist.profile_image_url = get_resized_image_url(
        artist.image_url, '300')
    data = schema.dump(artist)
    return J(data)


@current_app.route('/api/v1/me/artists/<artist_id>/albums/<album_id>', methods=['PATCH'])
@auth.requires_auth
def edit_album(artist_id, album_id):
   
    # load data and schema-validate
    schema = AlbumSchema()
    input_data = request.get_json() or {}
    try:
        data = schema.load(input_data)
        admin.sanitize.trim_strings(data)
    except ValidationError as err:
        return J(err.messages), 422

    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    # get album
    album = admin.albums.get_by_id(album_id)
    if album.artist.id != artist_id:
        raise Forbidden

    # save
    try:
        album = admin.albums.update(album, data)
    except admin.exceptions.ModelException as err:
        return J(to_error_object(err.message)), 422

    # return result
    album.profile_image_url = get_resized_image_url(
        album.image_url, '300x300')
    data = schema.dump(album)
    return J(data)


@current_app.route('/api/v1/me/artists/<artist_id>/image', methods=['POST'])
@auth.requires_auth
def add_artist_image(artist_id):

    try:
        file_data = get_posted_image(request)
    except admin.exceptions.InvalidData as err:
        return J(to_error_object(err.message)), 400
   
    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    # persist image
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
        album.thumbnail_image_url = get_resized_image_url(
            album.image_url, '80x80')
    data = AlbumSchema(many=True).dump(albums)
    return data


@current_app.route('/api/v1/me/artists/<artist_id>/albums', methods=['POST'])
@auth.requires_auth
def add_my_album(artist_id):
    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    schema = AlbumSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as err:
        return J(err.messages), 422

    try:
        newAlbum = admin.albums.add(artist, data)
    except admin.exceptions.ModelException as err:
        return J(to_error_object(err.message)), 422

    return J(schema.dump(newAlbum))


@current_app.route('/api/v1/me/artists/<artist_id>/albums/<album_id>')
@auth.requires_auth
def my_album_by_id(artist_id, album_id):
    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden
    
    album = admin.albums.get_by_id(album_id)
    if album.artist.id != artist_id:
        raise Forbidden

    album.profile_image_url = get_resized_image_url(
        album.image_url, '300')
    data = AlbumSchema().dump(album)
    return data

    
@current_app.route('/api/v1/me/artists/<artist_id>/albums/<album_id>/image', methods=['POST'])
@auth.requires_auth
def add_album_image(artist_id, album_id):

    try:
        file_data = get_posted_image(request)
    except InvalidData as err:
        return J(to_error_object(err.message)), 400

    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    # get album
    album = admin.albums.get_by_id(album_id)
    if album.artist.id != artist_id:
        raise Forbidden

    # persist image
    object_name = 'art/{0}-{1}/{2}-{3}/{2}-{4}.jpg'.format(
        artist.normalized_name, 
        artist.id,
        admin.names.safe_obj_name(album.title),
        album.id,
        ids.new_id()[:8])
    admin.files.save(file_data, object_name, content_type=admin.files.content_types['jpg'])
    # delete old file, if exists
    if album.image_url:
        admin.files.delete(album.image_url)

    # update album with new image_url
    admin.albums.update_image_url(artist_id=artist.id, album_id=album.id, image_url=object_name)

    # return entity with new profile_url
    album.profile_image_url = get_resized_image_url(
        object_name, '300x300')
    data = AlbumSchema().dump(album)
    return J(data)


@current_app.route('/api/v1/me/artists/<artist_id>/albums/<album_id>/tracks', methods=['POST'])
@auth.requires_auth
def add_album_track(artist_id, album_id):

    try:
        file_data = get_posted_audio(request)
    except admin.exceptions.InvalidData as err:
        return J(to_error_object(err.message)), 400

     # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    # get album
    album = admin.albums.get_by_id(album_id)
    if album.artist.id != artist_id:
        raise Forbidden

    # persist file
    track_title, extension = os.path.splitext(file_data.filename)
    safe_title = admin.names.safe_obj_name(track_title)
    object_name = 'art/{0}-{1}/{2}-{3}/{4}-{5}{6}'.format(
        artist.normalized_name, 
        artist.id,
        admin.names.safe_obj_name(album.title),
        album.id,
        safe_title,
        ids.new_id()[:8],
        extension)
    url = admin.files.save(file_data, object_name, content_type=admin.files.content_types.get(extension))

    try:
        track = admin.albums.create_track(album, track_title=track_title, audio_url=url)
    except admin.exceptions.ModelException as err:
        return J(to_error_object(err.message)), 422

    data = TrackSchema().dump(track)
    return J(data)


@current_app.route('/api/v1/me/artists/<artist_id>/albums/<album_id>/tracks/<track_id>/sort', methods=['POST'])
@auth.requires_auth
def sort_album_track(artist_id, album_id, track_id):

    try:
        direction = request.get_json()['data']['attributes']['direction']
    except Exception:
        return J(to_error_object('Invalid POST data')), 400

    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    # get album
    album = admin.albums.get_by_id(album_id)
    if album.artist.id != artist_id:
        raise Forbidden

    if not any(track.id == track_id for track in album.tracks):
        raise Forbidden

    try:
        admin.albums.sort_track(album, track_id, direction)
    except admin.exceptions.ModelException as err:
        return J(to_error_object(err.message)), 422

    data = AlbumSchema().dump(album)
    return J(data)

@current_app.route('/api/v1/me/artists/<artist_id>/albums/<album_id>/tracks/<track_id>', methods=['PATCH'])
@auth.requires_auth
def rename_track(artist_id, album_id, track_id):

    schema = TrackSchema()
    try:
        data = schema.load(request.get_json() or {})
        admin.sanitize.trim_strings(data)
    except ValidationError as err:
        return J(err.messages), 422

    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    # get album
    album = admin.albums.get_by_id(album_id)
    if album.artist.id != artist_id:
        raise Forbidden

    if not any(track.id == track_id for track in album.tracks):
        raise Forbidden

    try:
        track = admin.albums.change_track_title(album, track_id, new_title=data['title'])
    except admin.exceptions.ModelException as err:
        return J(to_error_object(err.message)), 422

    data =  TrackSchema().dump(track)
    return J(data)


@current_app.route('/api/v1/me/artists/<artist_id>/albums/<album_id>', methods=['DELETE'])
@auth.requires_auth
def delete_my_album(artist_id, album_id):

    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    # get album
    album = admin.albums.get_by_id(album_id)
    if album.artist.id != artist_id:
        raise Forbidden

    admin.albums.delete_album(album)

    return '', 204


@current_app.route('/api/v1/me/artists/<artist_id>/albums/<album_id>/tracks/<track_id>', methods=['DELETE'])
@auth.requires_auth
def delete_album_track(artist_id, album_id, track_id):

    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    # get album
    album = admin.albums.get_by_id(album_id)
    if album.artist.id != artist_id:
        raise Forbidden

    if not any(track.id == track_id for track in album.tracks):
        raise Forbidden

    admin.albums.delete_track(album, track_id)
    data = AlbumSchema().dump(album)
    return J(data)


@current_app.route('/api/v1/me/artists/<artist_id>/singles')
@auth.requires_auth
def my_artist_singles(artist_id):

    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    singles = admin.singles.list_for_artist(artist_id)

    data = SingleSchema(many=True).dump(singles)
    return J(data)


@current_app.route('/api/v1/me/artists/<artist_id>/singles', methods=['POST'])
@auth.requires_auth
def add_single(artist_id):

    try:
        file_data = get_posted_audio(request)
    except admin.exceptions.InvalidData as err:
        return J(to_error_object(err.message)), 400

     # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    # persist file
    single_title, extension = os.path.splitext(file_data.filename)
    safe_title = admin.names.safe_obj_name(single_title)
    object_name = 'art/{0}-{1}/{2}-{3}{4}'.format(
        artist.normalized_name, 
        artist.id,
        safe_title,
        ids.new_id()[:8],
        extension)
    url = admin.files.save(file_data, object_name, content_type=admin.files.content_types.get(extension))

    try:
        single = admin.singles.create(artist, single_title=single_title, audio_url=url)
    except admin.exceptions.ModelException as err:
        return J(to_error_object(err.message)), 422

    data = SingleSchema().dump(single)
    return J(data)


@current_app.route('/api/v1/me/artists/<artist_id>/singles/<single_id>', methods=['PATCH'])
@auth.requires_auth
def update_single(artist_id, single_id):
    
    schema = SingleSchema()
    try:
        data = schema.load(request.get_json() or {})
        admin.sanitize.trim_strings(data)
    except ValidationError as err:
        return J(err.messages), 422
    
    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    single = admin.singles.get_by_id(single_id)
    if not single:
        raise NotFound

    if single.artist.id != artist_id:
        raise Forbidden
    
    try:
        single = admin.singles.update(single, data)
    except admin.exceptions.ModelException as err:
        return J(to_error_object(err.message)), 422

    data = schema.dump(single)
    return J(data)



@current_app.route('/api/v1/me/artists/<artist_id>/singles/<single_id>/sort', methods=['POST'])
@auth.requires_auth
def sort_single(artist_id, single_id):

    try:
        direction = request.get_json()['data']['attributes']['direction']
    except Exception:
        return J(to_error_object('Invalid POST data')), 400

    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden
    
    try:
        singles = admin.singles.sort(artist, single_id, direction)
    except admin.exceptions.ModelException as err:
        return J(to_error_object(err.message)), 422

    data = SingleSchema(many=True).dump(singles)
    return J(data)


@current_app.route('/api/v1/me/artists/<artist_id>/singles/<single_id>', methods=['DELETE'])
@auth.requires_auth
def delete_single(artist_id, single_id):
    # get artist
    artist = admin.artists.by_id_for_owner(artist_id, current_user_email())
    if not artist:
        raise Forbidden

    single = admin.singles.get_by_id(single_id)
    if not single:
        raise NotFound

    if single.artist.id != artist_id:
        raise Forbidden
    
    try:
        admin.singles.delete(single)
    except admin.exceptions.ModelException as err:
        return J(to_error_object(err.message)), 422

    return '', 204


def to_error_object(message):
    """ make a JSONAPI error object from a single message string """
    return {'errors': [{'detail': message}]}


def get_posted_image(request, key='image_file'):
    if key not in request.files:
        raise admin.exceptions.InvalidData(message='no image file posted')

    file_data = request.files[key]
    if not file_data.filename.endswith('.jpg') and not file_data.filename.endswith(".jpeg"):
        raise admin.exceptions.InvalidData(message='Only JPEG files can be used for images')

    return file_data


def get_posted_audio(request, key='audio_file'):
    if key not in request.files:
        raise admin.exceptions.InvalidData(message='no audio file posted')

    file_data = request.files[key]

    return file_data





