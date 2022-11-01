from __future__ import absolute_import
import flask

from flask import request
from keg.web import BaseView as KegBaseView, route, rule

from keg_apps.extensions import gettext as _


blueprint = flask.Blueprint('routing', __name__)


class BaseView(KegBaseView):
    blueprint = blueprint


class VerbRouting(BaseView):
    """
        GET /verb-routing -> 'method get'
        POST /verb-routing -> 'method post'
    """

    def get(self):
        return _('method get')

    def post(self):
        return _('method post')


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
        return _('get some-route')


class ExplicitRouteAlt(KegBaseView):
    """
        /some-route-alt -> 'get some-route alt'

        Same as ExplicitRoute, but blueprint is not assigned in class definition. For route
        to be available, assign_blueprint must be called prior to blueprint registration.
    """
    rule('/some-route-alt')

    def get(self):
        return _('get some-route alt')


class HelloWorld(BaseView):
    """
        /hello-world -> 'Hello World'
        /hello-world/foo -> 'Hello Foo'
    """
    rule()
    rule('<name>')

    def get(self, name='World'):
        return _('Hello {name}', name=name)


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
        return _('post Hello {name}', name=name)

    def get(self, name):
        return _('Hello {name}', name=name)


class HelloReq(BaseView):
    """
        /hello-req -> 404
        /hello-req/foo -> 'Hello Foo'
    """
    # making the rule absolute disables the default rule that would have been created by the class.
    rule('/hello-req/<name>')

    def get(self, name):
        return _('Hello {name}', name=name)


class HelloReq2(BaseView):
    """
        /hello-req2 -> 404
        /hello-req2/foo -> 'Hello Foo'
    """
    # no absolute rule, but only one endpoint to use
    rule('<name>')

    def get(self, name):
        return _('Hello {name}', name=name)


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
        return _('list')

    @route()
    def create_get(self):
        return _('create get')

    @route(post_only=True)
    def create_post(self):
        return _('create post')

    @route('<int:car_id>', post=True)
    def edit(self, car_id):
        if request.method == 'GET':
            return _('form w/ data: {id}', id=car_id)
        else:
            return _('update car: {id}', id=car_id)

    @route('<int:ident>')
    def delete(self, ident):
        return _('delete: {ident}', ident=ident)


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
            return _('single')
        return _('list')

    def post(self):
        return _('create')

    def put(self, ticket_id):
        return _('update')

    def patch(self, ticket_id):
        return _('partial update')

    def delete(self, ticket_id):
        return _('delete')


class Misc(BaseView):
    rule('/misc')
    rule('foo')
    rule('/misc2')
    rule('bar', post_only=True)

    def get(self):
        return _('get')

    def post(self):
        return _('post')

    @route('/an-abs-url')
    def an_abs_url(self):
        return _('found me')

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
        return _('listing {class_name}', class_name=self.__class__.__name__)


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
