.. default-role:: code

Keg: more than Flask
####################

.. image:: https://codecov.io/github/level12/keg/coverage.svg?branch=master
    :target: https://codecov.io/github/level12/keg?branch=master

.. image:: https://img.shields.io/pypi/v/Keg.svg
    :target: https://img.shields.io/pypi/v/Keg.svg

.. image:: https://img.shields.io/pypi/l/keg.svg
    :target: https://img.shields.io/pypi/l/keg.svg

.. image:: https://img.shields.io/pypi/pyversions/keg.svg
    :target: https://img.shields.io/pypi/pyversions/keg.svg

.. image:: https://img.shields.io/pypi/status/Keg.svg
    :target: https://img.shields.io/pypi/status/Keg.svg

.. image:: https://ci.appveyor.com/api/projects/status/wm35hheykxs8851r
    :alt: AppVeyor Build
    :target: https://ci.appveyor.com/project/level12/keg-6gnlh

Keg is an opinionated but flexible web framework built on Flask and SQLAlchemy.


Keg's Goal
==========

The goal for this project is to encapsulate Flask best practices and libraries so devs can avoid
boilerplate and work on the important stuff.

We will lean towards being opinionated on the big things (like SQLAlchemy as our ORM) while
supporting hooks and customizations as much as possible.

Think North of Flask but South of Django.

Features
========

Default Logging Configuration
-----------------------------

We highly recommend good logging practices and, as such, a Keg application does basic setup of the
Python logging system:

- Sets the log level on the root logger to INFO
- Creates two handlers and assigns them to the root logger:

  - outputs to stderr
  - outputs to syslog

- Provides an optional json formatter

The thinking behind that is:

- In development, a developer will see log messages on stdout and doesn't have to monitor a file.
- Log messages will be in syslog by default and available for review there if no other action is
  taken by the developer or sysadmin.  This avoids the need to manage log placement, permissions,
  rotation, etc.
- It's easy to configure syslog daemons to forward log messages to different files or remote log
  servers and it's better to handle that type of need at the syslog level than in the app.
- Structured log files (json) provide metadata details in a easy-to-parse format and should be
  easy to generate.
- The options and output should be easily configurable from the app to account for different needs
  in development and deployed scenarios.
- Keg's logging setup should be easy to turn off and/or completely override for situations where it
  hurts more than it helps.

Installation
============

`pip install keg`


App Configuration
=================

CLI Command
-----------

The command `<myapp> develop config` will give detailed information about the files and objects
being used to configure an application.

Profile Priority
----------------

All configuration classes with the name `DefaultProfile` will be applied to the app's config
first.

Then, the configuration classes that match the "selected" profile will be applied on top of the
app's existing configuration. This makes the settings from the "selected" profile override any
settings from the `DefaultProfile.`

Practically speaking, any configuration that applies to the entire app regardless of what context
it is being used in will generally go in `myapp.config` in the `DefaultProfile` class.

Selecting a Configuration Profile
---------------------------------

The "selected" profile is the name of the objects that the Keg configuration handling code will
look for.  It should be a string.

A Keg app considers the "selected" profile as follows:

* If `config_profile` was passed into `myapp.init()` as an argument, use it as the
  selected profile.  The `--profile` cli option uses this method to set the selected profile and
  therefore has the highest priority.
* Look in the app's environment namespace for "CONFIG_PROFILE".  If found, use it.
* If running tests, use "TestProfile".  Whether or not the app is operating in this mode is
  controlled by the use of:

  - `myapp.init(use_test_profile=True)` which is used by `MyApp.testing_prep()`
  - looking in the app's environment namespace for "USE_TEST_PROFILE" which is used by
    `keg.testing.invoke_command()`

* Look in the app's main config file (`app.config`) and all it's other
  config files for the variable `DEFAULT_PROFILE`.  If found, use the value from the file with
  highest priority.


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


Components
==========

Keg components follow the paradigm of flask extensions, and provide some defaults for the
purpose of setting up model/view structure. Using components, a project may be broken down into
logical blocks, each having their own entities, blueprints, templates, tests, etc.

* Components need to be registered in config at `KEG_REGISTERED_COMPONENTS`

  * The path given here should be a full dotted path to the top level of the component

    * e.g. `my_app.components.blog`

  * At the top level of the component, `__component__` must be defined as an instance of KegComponent

    * Depending on the needs of the component, model and view discovery may be driven by the subclasses
      of KegComponent that have path defaults
    * Examples:

      * `__component__ = KegModelComponent('blog')`
      * `__component__ = KegViewComponent('blog')`
      * `__component__ = KegModelViewComponent('blog')`

* Component discovery

  * A component will attempt to load model and blueprints on app init
  * The default paths relative to the component may be modified or extended on the component's definition
  * Default model path in "model" components: `.model.entities`

    * Override via the component's `db_visit_modules` list of relative import paths

  * Default blueprint path for "view" components: `.views.component_bp`

    * Use the `create_named_blueprint` or `create_blueprint` helpers on the component's `__component__`
      to create blueprints with configured template folders
    * Override via the component's `load_blueprints` list

      * List elements are a tuple of the relative import path and the name of the blueprint attribute

    * Components have their own template stores, in a `templates` folder

      * Override the component's template path via the `template_folder` attribute

  * Paths may also be supplied to the constructor

    * e.g. `__component__ = KegComponent('blog', db_visit_modules=('.somewhere.else', ))`


Keg Development
===============

To develop on keg, begin by installing dependencies and running the tests::

    git clone https://github.com/level12/keg keg-src
    cd keg-src

    cp keg_apps/db/user-config-tpl.py ~/.config/keg_apps.db/keg_apps.db-config.py
    # edit the DB connection info in this file (you don't have to use vim):
    vim ~/.config/keg_apps.db/keg_apps.db-config.py

    # Create a virtualenv with a supported python version.  Activate it.
    pip install -e .[tests]
    pytest keg

You can then examine tox.ini for insights into our development process.  In particular, we:

* use `pytest` for testing (and coverage analysis)
* use `flake8` for linting

Preview Readme
--------------

When updating the readme, use `restview --long-description` to preview changes.

Links
=====

* Documentation: https://keg.readthedocs.io/en/stable/index.html
* Releases: https://pypi.org/project/Keg/
* Code: https://github.com/level12/keg
* Issue tracker: https://github.com/level12/keg/issues
* Questions & comments: http://groups.google.com/group/blazelibs

Current Status
==============

* Stable in a relatively small number of production environments.
* API is likely to change with smaller compatibility breaks happening more frequently than larger ones.
