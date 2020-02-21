Views
=====

While generic Flask views will certainly work in this framework, Keg provides a BaseView that
applies a certain amount of magic around route and blueprint setup. BaseView is based on Flask's
MethodView. Best practice is to set up a blueprint and attach the views to it via the `blueprint`
attribute. Be aware, BaseView will set up some route, endpoint, and template location defaults,
but these can be configured if needed.

Blueprint Setup
---------------

Adding views to a blueprint is accomplished via the `blueprint` attribute on the view. Note,
BaseView magic kicks in when the class is created, so assigning the blueprint later on will not
currently have the desired effect.

    import flask
    from keg.web import BaseView

    blueprint = flask.Blueprint('routing', __name__)


    class VerbRouting(BaseView):
        blueprint = blueprint

        def get(self):
            return 'method get'

Once the blueprint is created, you must attach it to the app via the `use_blueprints` app attribute:

    from keg.app import Keg
    from my_app.views import blueprint


    class MyApp(Keg):
        import_name = 'myapp'
        use_blueprints = (blueprint, )

Blueprints take some parameters for URL prefix and template path. BaseView will respect these when
generating URLs and finding templates:

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
its own `template_path` defined.

* `class MyBestView` in blueprint named "public" -> `<app>/templates/public/my_best_view.html`
* `class View2` in blueprint named "other" with template path "foo" -> `<app>/foo/view2.html`

A view may be given a `template_name` attribute to override the default filename, although the same
path is used for discovery:

    class TemplateOverride(BaseView):
        blueprint = blueprint
        template_name = 'my-special-template.html'

        def get(self):
            return self.render()

URL and Endpoint Calculation
----------------------------

BaseView has `calc_url` and `calc_endpoint` class methods which will allow the developer to avoid
hard-coding those types of values throughout the code. These methods will both produce the full
URL/endpoint, including the blueprint prefix (if any).

Route Generation
----------------

BaseView will, by default, create rules for views on their respective blueprints. Generally, this
is based on the view class name as a camel-case to dash-notation conversion:

* `class MyBestView` in blueprint named "public": `/my-best-view` -> `public.my-best-view`
* `class View2` in blueprint named "other" with URL prefix "foo": `/foo/view2` -> `other.view2`

Note that BaseView is a MethodView implementation, so methods named `get`, `post`, etc. will be
respected as the appropriate targets in the request/response cycle.

A view may be given a `url` attribute to override the default:

    class RouteOverride(BaseView):
        blueprint = blueprint
        url = '/something-other-than-the-default'

        def get(self):
            return self.render()

See `keg_apps/web/views/routing.py` for other routing possibilities that BaseView supports.
