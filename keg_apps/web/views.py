import flask

from keg.web import BaseView

public_blueprint = flask.Blueprint('public', __name__)


class PublicView(BaseView):
    blueprint = public_blueprint


class SomeView(PublicView):
    def get(self):
        return 'hi from SomeView'


class Home(PublicView):
    url = '/'

    def get(self):
        return 'home'


class Hello(PublicView):
    urls = ['/hello', '/hello/<name>']

    def get(self, name='World'):
        return 'Hello {}'.format(name)


class Template1(PublicView):
    def get(self):
        self.assign('name', 'world')


class Template2(PublicView):
    template_name = 'public/template-too.html'

    def get(self):
        pass

