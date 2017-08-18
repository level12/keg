from __future__ import absolute_import

import warnings

import flask
from flask.config import ConfigAttribute
from six.moves import range
from werkzeug.datastructures import ImmutableDict

from keg.blueprints import keg as kegbp
import keg.cli
import keg.config
from keg.ctx import KegRequestContext
import keg.logging
import keg.signals as signals
from keg.templating import _keg_default_template_ctx_processor, AssetsExtension
from keg.utils import classproperty, visit_modules, hybridmethod
import keg.web


class KegAppError(Exception):
    pass


class Keg(flask.Flask):
    import_name = None
    use_blueprints = ()
    oauth_providers = ()
    keyring_enabled = ConfigAttribute('KEG_KEYRING_ENABLE')
    config_class = keg.config.Config
    logging_class = keg.logging.Logging
    keyring_manager_class = None

    _cli = None
    cli_loader_class = keg.cli.CLILoader

    db_enabled = False
    db_visit_modules = ['.model.entities']
    db_manager = None

    jinja_options = ImmutableDict(
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_', AssetsExtension]
    )

    template_filters = ImmutableDict()
    template_globals = ImmutableDict()

    visit_modules = False

    _init_ran = False

    def __init__(self, import_name=None, static_path=None, static_url_path=None,
                 static_folder='static', template_folder='templates', instance_path=None,
                 instance_relative_config=False, config=None):

        # flask requires an import name, so we should too.
        if import_name is None and self.import_name is None:
            raise KegAppError('Please set the "import_name" attribute on your app class or pass it'
                              ' into the app instance.')

        # passed in value takes precedence
        import_name = import_name or self.import_name

        self.keyring_manager = None
        self._init_config = config or {}

        flask.Flask.__init__(self, import_name, static_path=static_path,
                             static_url_path=static_url_path, static_folder=static_folder,
                             template_folder=template_folder, instance_path=instance_path,
                             instance_relative_config=instance_relative_config)

    def make_config(self, instance_relative=False):
        """
            Needed for Flask <= 0.10.x so we can set the configuration class
            being used.  Once 0.11 comes out, Flask supports setting the config_class on the app.
        """
        root_path = self.root_path
        if instance_relative:
            root_path = self.instance_path
        return self.config_class(root_path, self.default_config)

    def init(self, config_profile=None, use_test_profile=False, config=None):
        if self._init_ran:
            raise KegAppError('init() already called on this instance')
        self._init_ran = True

        self.init_config(config_profile, use_test_profile, config)
        self.init_logging()
        self.init_keyring()
        self.init_oath()
        self.init_error_handling()
        self.init_extensions()
        self.init_routes()
        self.init_blueprints()
        self.init_jinja()
        self.init_visit_modules()

        self.on_init_complete()
        signals.app_ready.send(self)
        signals.init_complete.send(self)

        # return self for easy chaining, i.e. app = MyKegApp().init()
        return self

    def on_init_complete(self):
        """ For subclasses to override """
        pass

    def init_config(self, config_profile, use_test_profile, config):
        init_config = self._init_config.copy()
        init_config.update(config or {})

        self.config.init_app(config_profile, self.import_name, self.root_path, use_test_profile)

        self.config.update(init_config)

        signals.config_ready.send(self)
        signals.config_complete.send(self)
        self.on_config_complete()

    def on_config_complete(self):
        """ For subclasses to override """
        pass

    def init_keyring(self):
        # do keyring substitution
        if self.keyring_enabled:
            from keg.keyring import Manager, keyring
            if keyring is None:
                warnings.warn('Keyring substitution is enabled, but the keyring package is not'
                              ' installed.  Please install the keyring package (pip install'
                              ' keyring) or disable keyring support by setting `KEG_KEYRING_ENABLE'
                              ' = False` in your configuration profile.')
                return

            self.keyring_manager = Manager(self)
            self.keyring_manager.substitute(self.config)

    def init_extensions(self):
        self.init_db()

    def db_manager_cls(self):
        from keg.db import DatabaseManager
        return DatabaseManager

    def init_db(self):
        if self.db_enabled:
            cls = self.db_manager_cls()
            self.db_manager = cls(self)

    def init_blueprints(self):
        # TODO: probably want to be selective about adding our blueprint
        self.register_blueprint(kegbp)
        for blueprint in self.use_blueprints:
            self.register_blueprint(blueprint)

    def init_logging(self):
        self.logging = self.logging_class(self.config)
        self.logging.init_app()

    def init_error_handling(self):
        # handle status codes
        generic_errors = range(500, 506)
        for err in generic_errors:
            self.errorhandler(err)(self.handle_server_error)

        # utility to abort responses
        self.errorhandler(keg.web.ImmediateResponse)(keg.web.handle_immediate_response)

    def init_oath(self):
        # if no providers are listed, then we don't need to do anything else
        if not self.oauth_providers:
            return

        from keg.oauth import oauthlib, bp, manager
        self.register_blueprint(bp)
        oauthlib.init_app(self)
        manager.register_providers(self.oauth_providers)

    def init_jinja(self):
        self.jinja_env.filters.update(self.template_filters)

        # template_context_processors is supposed to be functions that return dictionaries where
        # the key is the name of the template variable and the value is the value.
        # First, add Keg defaults
        self.template_context_processors[None].append(_keg_default_template_ctx_processor)
        self.template_context_processors[None].append(lambda: self.template_globals)

    def init_visit_modules(self):
        if self.visit_modules:
            visit_modules(self.visit_modules, self.import_name)

    def handle_server_error(self, error):
        # send_exception_email()
        return '500 SERVER ERROR<br/><br/>administrators notified'

    def request_context(self, environ):
        return KegRequestContext(self, environ)

    def _cli_getter(cls):  # noqa: first argument is not self in this context due to @classproperty
        if cls._cli is None:
            cal = cls.cli_loader_class(cls)
            cls._cli = cal.create_group()
        return cls._cli
    cli = classproperty(_cli_getter, ignore_set=True)

    @classmethod
    def environ_key(cls, key):
        # App names often have periods and it is not possibe to export an
        # environment variable with a period in it.
        name = cls.import_name.replace('.', '_').upper()
        return '{}_{}'.format(name, key.upper())

    @classmethod
    def testing_prep(cls, **config):
        """
            Make sure an instance of this class exists in a state that is ready for testing to
            commence.

            Trigger `signal.testing_run_start` the first time this method is called for an app.
        """
        # For now, do the import here so we don't have a hard dependency on WebTest
        from keg.testing import ContextManager
        if cls is Keg:
            raise TypeError('Don\'t use testing_prep() on Keg.  Create a subclass first.')
        cm = ContextManager.get_for(cls)

        # if the context manager's app isn't ready, that means this will be the first time the app
        # is instantiated.  That seems like a good indicator that tests are just beginning, so it's
        # safe to trigger the signal.  We don't want the signal to fire every time b/c
        # testing_prep() can be called more than once per test run.
        trigger_signal = not cm.is_ready()
        cm.ensure_current(config)

        if trigger_signal:
            signals.testing_run_start.send(cm.app)

        return cm.app

    def make_shell_context(self):
        return {}

    @property
    def logger(self):
        return self.logging.app_logger

    @hybridmethod
    def route(self, rule, **options):
        """ Same as Flask.route() and will be used when in an instance context. """
        return super(Keg, self).route(rule, **options)

    @route.classmethod
    def route(cls, rule, **options):  # noqa
        """
            Enable .route() to be used in a class context as well.  E.g.:

            KegApp.route('/something'):
            def view_something():
                pass
        """
        def decorator(f):
            if not hasattr(cls, '_routes'):
                cls._routes = []
            cls._routes.append((f, rule, options))
            return f
        return decorator

    def init_routes(self):
        if not hasattr(self, '_routes'):
            return
        for func, rule, options in self._routes:
            # We follow the same logic here as Flask.route() decorator.
            endpoint = options.pop('endpoint', None)
            self.add_url_rule(rule, endpoint, func, **options)


@signals.init_complete.connect
def flask_wtf_bugfix(app):
    """ Needed until https://github.com/lepture/flask-wtf/issues/301 is fixed & released. """
    if not app.config.get('FIX_FLASK_WTF_BUG', True):
        return

    try:
        import flask_wtf
    except ImportError:
        return

    version = tuple(map(lambda x: int(x), flask_wtf.__version__.split('.')))

    if version < (0, 14, 0):
        return

    @app.teardown_request
    def cleanup_csrf_cache(error):
        if 'csrf_token' in flask.g:
            del flask.g.csrf_token
