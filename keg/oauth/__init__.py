from __future__ import absolute_import

from flask import url_for, session, request, jsonify, Blueprint, flash, current_app
from flask_oauthlib.client import OAuth

from keg.web import redirect

oauthlib = OAuth()


class OAuthError(Exception):
    pass


class Provider(object):
    def authorize(self, **kwargs):
        return self.remote_app.authorize(**kwargs)

    def get(self, *args):
        return self.remote_app.get(*args)


class Google(Provider):
    def __init__(self):
        self.remote_app = oauthlib.remote_app(
            'google',
            request_token_params={
                'scope': 'https://www.googleapis.com/auth/userinfo.email'
            },
            base_url='https://www.googleapis.com/oauth2/v1/',
            request_token_url=None,
            access_token_method='POST',
            access_token_url='https://accounts.google.com/o/oauth2/token',
            authorize_url='https://accounts.google.com/o/oauth2/auth',
            app_key='KEG_OAUTH_GOOGLE',
        )
        self.remote_app.tokengetter(manager.token)

    def authorized_response(self):
        resp = self.remote_app.authorized_response()

        if isinstance(resp, Exception):
            flash(str(resp), 'error')
        elif resp is None:
            error_message = 'authentication failure: reason=%s error=%s' % (
                request.args.get('error_reason', 'unknown'),
                request.args.get('error', 'unknown')
            )
            flash(error_message, 'error')
        else:
            return resp['access_token']


class Manager(object):
    provider_classes = {
        'google': Google,
    }

    def __init__(self):
        self.providers = {}

    def register_providers(self, providers):
        for provider in providers:
            if provider not in self.provider_classes:
                # if it's not a string of a known provider, then assume its a Provider instance
                self.providers[provider.name] = provider()
            else:
                self.providers[provider] = self.provider_classes[provider]()

    def session_key(self, key):
        return '{}.oauth.{}'.format(current_app.name, key)

    def provider(self, provider_key=None):
        provider_key = provider_key or session[self.session_key('provider')]
        try:
            return self.providers[provider_key]
        except KeyError:
            raise OAuthError('Provier "{}" has not been registered.'.format(provider_key))

    def authorize(self, provider, callback):
        session[self.session_key('provider')] = provider
        return self.provider(provider).authorize(callback=callback)

    def authorized_response(self):
        provider = session[self.session_key('provider')]
        token = self.provider(provider).authorized_response()
        if token:
            session[self.session_key('token')] = token

    def authenticated(self):
        return bool(session.get(self.session_key('token'), None))

    def get(self, *args):
        return self.provider().get(*args)

    def userinfo(self):
        return self.provider().userinfo()

    def clear(self):
        token_key = self.session_key('token')
        if token_key in session:
            del session[token_key]

    def token(self):
        return session[self.session_key('token')]

manager = Manager()

bp = Blueprint('oauth', __name__, url_prefix='/oauth')


@bp.route('/userinfo')
def userinfo():
    if manager.authenticated():
        return jsonify(manager.userinfo())
    return redirect('LOGIN')


@bp.route('/login/<provider>')
def login(provider):
    callback_url = url_for('.callback', _external=True)
    return manager.authorize(provider, callback_url)


@bp.route('/logout')
def logout():
    manager.clear()
    return redirect('AFTER_LOGOUT')


@bp.route('/callback')
def callback():
    manager.authorized_response()
    return redirect('AFTER_LOGIN')
