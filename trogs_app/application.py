import os

import flask_resize
from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, session, url_for
from six.moves.urllib.parse import urlencode

import views

application = Flask(__name__)
application.secret_key = 'Troglodytes42'

application.config['RESIZE_STORAGE_BACKEND'] = 's3'
application.config['RESIZE_S3_BUCKET'] = os.environ['AWS_CONTENT_BUCKET']
resize = flask_resize.Resize(application)

oauth = OAuth(application)

auth0 = oauth.register(
    'auth0',
    client_id=os.environ['AUTH0_CLIENT_ID'],
    client_secret=os.environ['AUTH0_CLIENT_SECRET'],
    api_base_url=os.environ['AUTH0_API_BASE_URL'],
    access_token_url=os.environ['AUTH0_ACCESS_TOKEN_URL'],
    authorize_url=os.environ['AUTH0_AUTHORIZE_URL'],
    client_kwargs={
        'scope': 'openid profile email',
    }
)


@application.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri=url_for('callback', _external=True))


@application.route('/callback')
def callback():
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()
    #print('userinfo', userinfo)

    session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo.get('name'),
        'email': userinfo.get('email')
    }
    return redirect(url_for('home'))


@application.route('/logout')
def logout():
    session.clear()
    params = {
        'returnTo': url_for('home', _external=True),
        'client_id': os.environ['AUTH0_CLIENT_ID']
    }
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))


def favicon():
    return application.send_static_file('favicon.ico')


application.add_url_rule('/', view_func=views.home)
application.add_url_rule('/artist/<id>', view_func=views.artist)
application.add_url_rule('/album/<id>', view_func=views.album)
application.add_url_rule('/track/<id>', view_func=views.track)
application.add_url_rule('/favicon.ico', view_func=favicon)

# run the app.
if __name__ == "__main__":
    application.run()
