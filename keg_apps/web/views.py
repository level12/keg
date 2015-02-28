import flask

from keg.web import BaseView, route

public_blueprint = flask.Blueprint('public', __name__)


class PublicView(BaseView):
    blueprint = public_blueprint


class MethodRouting(PublicView):

    def get(self):
        return 'method get'

    def post(self):
        return 'method post'


class ExplicitRoute(PublicView):
    url = '/'

    def get(self):
        return 'get explicit'


class Hello(PublicView):

    @route('<name>')
    def get(self, name='World'):
        return 'Hello {}'.format(name)


class Template1(PublicView):
    def get(self):
        self.assign('name', 'world')


class Template2(PublicView):
    template_name = 'public/template-two.html'

    def get(self):
        pass


class Routing(PublicView):

    @route(post=True)
    def create(self):
        if flask.request.method == 'GET':
            return 'create get'
        else:
            return 'create post'

    @route(index=True)
    def read(self):
        return 'read'

    @route('<int:ident>', post=True)
    def update(self, ident):
        if flask.request.method == 'GET':
            return 'get update {!r}'.format(ident)
        else:
            return 'post update {!r}'.format(ident)

    @route('<int:ident>')
    def delete(self, ident):
        pass

class RoutingSubclass(Routing):
    pass
