import os

import flask_resize
from flask import Flask, redirect, session
import views, auth

application = Flask(__name__)
application.secret_key = 'Troglodytes42'

application.config['RESIZE_STORAGE_BACKEND'] = 's3'
application.config['RESIZE_S3_BUCKET'] = os.environ['AWS_CONTENT_BUCKET']
resize = flask_resize.Resize(application)

def favicon():
    return application.send_static_file('favicon.ico')

application.add_url_rule('/', view_func=views.home)
application.add_url_rule('/artist/<id>', view_func=views.artist)
application.add_url_rule('/album/<id>', view_func=views.album)
application.add_url_rule('/track/<id>', view_func=views.track)
application.add_url_rule('/favicon.ico', view_func=favicon)

auth_routes = auth.create_routes(application)
[ application.add_url_rule(rule, view_func=auth_routes[rule]) for rule in auth_routes.keys()]


# run the app.
if __name__ == "__main__":
    application.run()
