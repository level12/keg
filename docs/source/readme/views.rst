Views
=====

While generic Flask views will certainly work in this framework, Keg provides a BaseView that
applies a certain amount of magic around route and blueprint setup. BaseView is based on Flask's
MethodView. Best practice is to set up a blueprint and attach the views to it via the ``blueprint``
attribute. Be aware, BaseView will set up some route, endpoint, and template location defaults,
but these can be configured if needed.

Blueprint Setup
---------------

Adding views to a blueprint is accomplished via the ``blueprint`` attribute on the view. Note,
BaseView magic kicks in when the class is created, so assigning the blueprint later on will not
currently have the desired effect::

    import flask
    from keg.web import BaseView

    blueprint = flask.Blueprint('routing', __name__)


    class VerbRouting(BaseView):
        blueprint = blueprint

        def get(self):
            return 'method get'

Once the blueprint is created, you must attach it to the app via the ``use_blueprints`` app attribute::

    from keg.app import Keg
    from my_app.views import blueprint


    class MyApp(Keg):
        import_name = 'myapp'
        use_blueprints = (blueprint, )

Blueprints take some parameters for URL prefix and template path. BaseView will respect these when
generating URLs and finding templates::

    blueprint = flask.Blueprint(
        'custom',
        __name__,
        template_folder='../templates/specific-path',
        url_prefix='/tanagra')

    class BlueprintTest(BaseView):
        # template "blueprint_test.html" will be expected in specific-path
        # endpoint is custom.blueprint-test
        # URL is /tanagra/blueprint-test
        blueprint = blueprint

        def get(self):
            return self.render()

Template Discovery
------------------

To avoid requiring the developer to configure all the things, BaseView will attempt to discover the
correct template for a view, based on the view class name. Generally, this is a camel-case to
underscore-notation conversion. Blueprint name is included in the path, unless the blueprint has
its own ``template_path`` defined.

* ``class MyBestView`` in blueprint named "public" -> ``<app>/templates/public/my_best_view.html``
* ``class View2`` in blueprint named "other" with template path "foo" -> ``<app>/foo/view2.html``

A view may be given a ``template_name`` attribute to override the default filename, although the same
path is used for discovery::

    class TemplateOverride(BaseView):
        blueprint = blueprint
        template_name = 'my-special-template.html'

        def get(self):
            return self.render()

URL and Endpoint Calculation
----------------------------

BaseView has ``calc_url`` and ``calc_endpoint`` class methods which will allow the developer to avoid
hard-coding those types of values throughout the code. These methods will both produce the full
URL/endpoint, including the blueprint prefix (if any).

Route Generation
----------------

BaseView will, by default, create rules for views on their respective blueprints. Generally, this
is based on the view class name as a camel-case to dash-notation conversion:

* ``class MyBestView`` in blueprint named "public": ``/my-best-view`` -> ``public.my-best-view``
* ``class View2`` in blueprint named "other" with URL prefix "foo": ``/foo/view2`` -> ``other.view2``

Note that BaseView is a MethodView implementation, so methods named ``get``, ``post``, etc. will be
respected as the appropriate targets in the request/response cycle.

A view may be given a ``url`` attribute to override the default::

    class RouteOverride(BaseView):
        blueprint = blueprint
        url = '/something-other-than-the-default'

        def get(self):
            return self.render()

See ``keg_apps/web/views/routing.py`` for other routing possibilities that BaseView supports.

Class View Lifecycle
--------------------

Keg views use Flask's ``dispatch_request`` to call several methods walking a view through its
response cycle. As the methods progress, assumptions may be built for access, availability,
etc. Many of these methods will not normally be present on a view.

The view lifecycle is as follows:

* ``process_calling_args``

  * Gather arguments from the route definition and the query string
  * If ``expected_qs_args`` is set on the view, look for these arguments in the query string
  * URL arguments from the route definition have precedence over GET args in the query string
  * Arguments are processed once, then stored on the view

* ``pre_auth``

  * Meant for actions that should take place before a user/session has been verified
  * Assumptions: calling args

* ``check_auth``

  * Meant to verify the user/session has access to this resource
  * Failure at this point should take appropriate action in the method itself (403, 401, etc.)
  * Extensions such as keg-auth leverage this method to insert permission-based authorization into the view cycle
  * Assumptions: calling args

* ``pre_loaders``

  * Authentication/authorization has passed, but we haven't loaded any related view dependencies
  * Assumptions: calling args, auth

* Loader methods

  * Any method on the view ending with ``_loader`` is called with args
  * Return value of the method is stored with the calling args, keyed by the method name

    * e.g. a method named ``record_loader`` will set a value in calling args for ``record``

  * Methods folliwng this in the lifecycle can use the newly-set arg
  * If no value is returned, Keg assumes a required dependency could not be loaded and returns a 404 response
  * Order of execution of a view's loaders may not be assumed
  * Assumptions: calling args, auth

* ``pre_method``

  * Ideal method for running code shared by all response methods (e.g. ``get``, ``post``, etc.)
  * Assumptions: calling args, auth, loader args

* Responding method

  * The method used here is generally the lowercase of the request method (e.g. ``get``, ``post``, etc.)
  * If the request method is HEAD, but there is no ``head`` method, Keg looks for ``get`` instead
  * This method may return the view's response
  * Assumptions: calling args, auth, loader args

* If responding method does not return a reponse:

  * I.e. the responding method returned something falsy that isn't an empty string
  * ``pre_render``

    * Assumptions: calling args, auth, loader args

  * ``render``

    * Returns a response object
    * By default, renders the template with args assigned on the view
    * See Template Discovery above

* ``pre_response``

  * A response has been generated, but has not been sent yet
  * The response is included as the ``_response`` arg for this method
  * The response should not be assumed to be mutable
  * If a different response should be sent, return that response from this method
  * Assumptions: calling args, auth, loader args, response (from responding method or render)
