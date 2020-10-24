import os

import flask_resize
from flask import Flask, redirect, session

application = Flask(__name__)
application.secret_key = os.environ["FLASK_SECRET_KEY"]

application.config['RESIZE_STORAGE_BACKEND'] = 's3'
application.config['RESIZE_S3_BUCKET'] = os.environ['AWS_CONTENT_BUCKET']

# the following resize config keys should not need to be set normally
# since the boto3 client will get this from the currently executing profile.
# Adding the option to explicitly set them so that we can override the current
# AWS profile and access remote S3, while still using the local aws config profile for other services (dynamodb).
if 'AWS_CONTENT_ACCESS_KEY_ID' in os.environ:
    application.config['RESIZE_S3_ACCESS_KEY'] = os.environ['AWS_CONTENT_ACCESS_KEY_ID']

if 'AWS_CONTENT_SECRET_ACCESS_KEY' in os.environ:
    application.config['RESIZE_S3_SECRET_KEY'] = os.environ['AWS_CONTENT_SECRET_ACCESS_KEY']

if 'AWS_CONTENT_REGION' in os.environ:
    application.config['RESIZE_S3_REGION'] = os.environ['AWS_CONTENT_REGION']

resize = flask_resize.Resize(application)

with application.app_context():
    import views, auth, api

@application.route('/favicon.ico')
def favicon():
    return application.send_static_file('favicon.ico')

# run the app.
if __name__ == "__main__":
    application.run()
