import os

import flask_resize
from flask import Flask, redirect, session

application = Flask(__name__)
application.secret_key = 'Troglodytes42'

application.config['RESIZE_STORAGE_BACKEND'] = 's3'
application.config['RESIZE_S3_BUCKET'] = os.environ['AWS_CONTENT_BUCKET']
resize = flask_resize.Resize(application)

with application.app_context():
    import views, auth

@application.route('/favicon.ico')
def favicon():
    return application.send_static_file('favicon.ico')

# run the app.
if __name__ == "__main__":
    application.run()
