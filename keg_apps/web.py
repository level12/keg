from __future__ import absolute_import
from __future__ import unicode_literals

import flask
from keg.app import Keg
from keg.web import PublicView


class WebView(PublicView):
    blueprint = flask.Blueprint('web', __name__)


class WebApp(Keg):
    import_name = __name__
    use_blueprints = [WebView.blueprint]


class SomeView(WebView):
    def get(self):
        return 'hi from SomeView'


class Hello(WebView):
    urls = ['/hello', '/hello/<name>']

    def get(self, name='World'):
        return 'Hello {}'.format(name)
