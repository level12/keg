from __future__ import absolute_import
from __future__ import unicode_literals
import flask

from keg.web import BaseView, route, rule

public_blueprint = flask.Blueprint('public', __name__)


class PublicView(BaseView):
    blueprint = public_blueprint


class VerbRouting(PublicView):
    """
        GET /verb-routing -> 'method get'
        POST /verb-routing -> 'method post'
    """

    def get(self):
        return 'method get'

    def post(self):
        return 'method post'


class VerbRoutingSub(VerbRouting):
    """
        Same as VerbRouting
    """


class ExplicitRoute(PublicView):
    """
        /explicit-route -> 404
        /some-route/foo -> 'get some-route'
    """
    # absolute URL indicates the default class URL will not be generated
    rule('/some-route')

    def get(self):
        return 'get some-route'


class HelloWorld(PublicView):
    """
        /hello -> 'Hello World'
        /hello/foo -> 'Hello Foo'
    """
    # relative URL indicates this route should be appended to the default rule for the class
    rule('<name>')

    def get(self, name='World'):
        return 'Hello {}'.format(name)


class HWRuleDefault(PublicView):
    """
        GET /hwrd -> 'Hello RD'
        GET /hwrd/foo -> 'Hello Foo'
        POST /hwrd -> 'post Hello RD'
        POST /hwrd-> 'post Hello Foo'
    """
    # Since the default rule needs to have defaults, you need to define it and not rely on the
    # auto-generated one.
    rule('/hwrd', defaults={'name': 'RD'})
    rule('<name>')

    def post(self, name):
        return 'post Hello {}'.format(name)

    def get(self, name):
        return 'Hello {}'.format(name)


class HelloReqOpt1(PublicView):
    """
        /hello-req-opt1 -> 404
        /hello-req-opt1/foo -> 'Hello Foo'
    """
    rule('/hello-req-opt1/<name>')

    def get(self, name):
        return 'Hello {}'.format(name)

#class Cars(PublicView):
#    """
#        CRUD for a model/entity
#
#        GET /cars/list - show list of cars that can be managed
#        GET /cars/create - show empty car form
#        POST /cars/create - create a new car
#        GET /cars/edit/12 - show car form w/ data
#        POST /cars/edit/12 - update car 12
#        GET /cars/delete/12 - deletes car 12
#    """
#
#    @route()
#    def list(self):
#        return 'list'
#
#    @route()
#    def create_get(self):
#        return 'create get'
#
#    @route(post_only=True)
#    def create_post(self):
#        return 'create post'
#
#    @route('<int:car_id>', post=True)
#    def edit(self, car_id, http_method):
#        if http_method == 'GET':
#            return 'form w/ data: {}'.format(car_id)
#        else:
#            return 'update car: {}'.format(car_id)
#
#    @route('<int:ident>')
#    def delete(self, ident):
#        return 'delete {}'.format(ident)
#
#
#class Tickets(PublicView):
#    """
#        REST API Example
#
#        GET /tickets - Retrieves a list of tickets
#        GET /tickets/12 - Retrieves a specific ticket
#        POST /tickets - Creates a new ticket
#        PUT /tickets/12 - Updates ticket #12
#        PATCH /tickets/12 - Partially updates ticket #12
#        DELETE /tickets/12 - Deletes ticket #12
#    """
#    rule('<int:ticket_id>')
#
#    def get(self, ticket_id=None):
#        if ticket_id:
#            return 'single'
#        return 'list'
#
#    def post(self):
#        return 'create'
#
#    def put(self, ticket_id):
#        return 'update'
#
#    def patch(self, ticket_id):
#        return 'partial update'
#
#    def delete(self, ticket_id):
#        return 'delete'


#class Unsure(PublicView):
#    """
#        GET /hwrd -> 'Hello RD'
#        GET /hwrd/foo -> 'Hello Foo'
#        POST /hwrd -> 'Hello RD'
#        POST /hwrd-> 'Hello Foo'
#    """
#    # Since the default rule needs to have defaults, you need to define it and not rely on the
#    # auto-generated one.
#    rule('/hwrd')
#    rule('/foo')
#    rule('<name>')  # which rule does this belong too?


class Template1(PublicView):
    def get(self):
        self.assign('name', 'world')


class Template2(PublicView):
    template_name = 'public/template-two.html'

    def get(self):
        pass


