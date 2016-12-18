from __future__ import absolute_import
import flask

from flask import request
from keg.web import BaseView as KegBaseView, route, rule

blueprint = flask.Blueprint('routing', __name__)


class BaseView(KegBaseView):
    blueprint = blueprint


class VerbRouting(BaseView):
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


class ExplicitRoute(BaseView):
    """
        /explicit-route -> 404
        /some-route/foo -> 'get some-route'
    """
    # absolute URL indicates the default class URL will not be generated
    rule('/some-route')

    def get(self):
        return 'get some-route'


class HelloWorld(BaseView):
    """
        /hello -> 'Hello World'
        /hello/foo -> 'Hello Foo'
    """
    # relative URL indicates this route should be appended to the default rule for the class
    rule('<name>')

    def get(self, name='World'):
        return 'Hello {}'.format(name)


class HWRuleDefault(BaseView):
    """
        GET /hwrd -> 'Hello RD'
        GET /hwrd/foo -> 'Hello Foo'
        POST /hwrd -> 'post Hello RD'
        POST /hwrd-> 'post Hello Foo'
    """
    # Since the default rule needs to have defaults, you need to define it and not rely on the
    # auto-generated one.
    rule('/hwrd', post=True, defaults={'name': 'RD'})
    rule('<name>', post=True)

    def post(self, name):
        return 'post Hello {}'.format(name)

    def get(self, name):
        return 'Hello {}'.format(name)


class HelloReq(BaseView):
    """
        /hello-req -> 404
        /hello-req/foo -> 'Hello Foo'
    """
    # making the rule absolute disables the default rule that would have been created by the class.
    rule('/hello-req/<name>')

    def get(self, name):
        return 'Hello {}'.format(name)


class Cars(BaseView):
    """
        CRUD for a model/entity

        GET /cars/list - show list of cars that can be managed
        GET /cars/create - show empty car form
        POST /cars/create - create a new car
        GET /cars/edit/12 - show car form w/ data
        POST /cars/edit/12 - update car 12
        GET /cars/delete/12 - deletes car 12
    """

    @route()
    def list(self):
        return 'list'

    @route()
    def create_get(self):
        return 'create get'

    @route(post_only=True)
    def create_post(self):
        return 'create post'

    @route('<int:car_id>', post=True)
    def edit(self, car_id):
        if request.method == 'GET':
            return 'form w/ data: {}'.format(car_id)
        else:
            return 'update car: {}'.format(car_id)

    @route('<int:ident>')
    def delete(self, ident):
        return 'delete: {}'.format(ident)


class Tickets(BaseView):
    """
        REST API Example

        GET /tickets - Retrieves a list of tickets
        GET /tickets/12 - Retrieves a specific ticket
        POST /tickets - Creates a new ticket
        PUT /tickets/12 - Updates ticket #12
        PATCH /tickets/12 - Partially updates ticket #12
        DELETE /tickets/12 - Deletes ticket #12
    """
    rule('/tickets', methods=['GET', 'POST'])
    rule('<int:ticket_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])

    def get(self, ticket_id=None):
        if ticket_id:
            return 'single'
        return 'list'

    def post(self):
        return 'create'

    def put(self, ticket_id):
        return 'update'

    def patch(self, ticket_id):
        return 'partial update'

    def delete(self, ticket_id):
        return 'delete'


class Misc(BaseView):
    rule('/misc')
    rule('foo')
    rule('/misc2')
    rule('bar', post_only=True)

    def get(self):
        return 'get'

    def post(self):
        return 'post'

    @route('/an-abs-url')
    def an_abs_url(self):
        return 'found me'

    @route('8')
    @route('9')
    def two_routes(self):
        return '17'


class CrudBase(KegBaseView):
    """
        Testing a view that is intended to be used as an abstract class: it should be inherited
        but will never be instantiated itself.

        This is similiar to BaseView, except that this class is intended to represent a class that
        isn't confined to a certain blueprint, but intended to give similar functionality in a way
        that can be used in/with different blueprints.

        Pain points that this identifies:

            - This class itself should be created without throwing an exception due to not having
              a blueprint.
            - The creation of this class should not cause any application routes to be defined.
            - The creation of a subclass of this class should result in routes for the subclass
              being created.
    """
    @route()
    def list(self):
        return 'listing {}'.format(self.__class__.__name__)


class Trucks(CrudBase):
    """
        CRUD for a model/entity

        GET /trucks/list
    """
    blueprint = blueprint


class Planes(CrudBase):
    """
        CRUD for a model/entity

        GET /planes/list
    """
    blueprint = blueprint
