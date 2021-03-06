import os

from authlib.integrations.flask_client import OAuth
from flask import redirect, session, url_for, current_app
from six.moves.urllib.parse import urlencode
from functools import wraps

oauth = OAuth(current_app)

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


@current_app.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri=url_for('callback', _external=True))


@current_app.route('/callback')
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
    return redirect(url_for('create'))


@current_app.route('/logout')
def logout():
    session.clear()
    params = {
        'returnTo': url_for('home', _external=True),
        'client_id': os.environ['AUTH0_CLIENT_ID']
    }
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'profile' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated
