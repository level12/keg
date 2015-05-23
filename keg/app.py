from __future__ import absolute_import
from __future__ import unicode_literals

import warnings

from blazeutils.strings import randchars
import flask
from flask.config import ConfigAttribute
from six.moves import range

from keg.blueprints import keg as kegbp
import keg.cli
import keg.config
import keg.logging
import keg.signals as signals
from keg.utils import classproperty
import keg.web


class KegAppError(Exception):
    pass


class Keg(flask.Flask):
    import_name = None
    use_blueprints = []
    oauth_providers = []
    keyring_enabled = ConfigAttribute('KEG_KEYRING_ENABLE')
    config_class = keg.config.Config
    logging_class = keg.logging.Logging
    keyring_manager_class = None

    db_enabled = False
    db_visit_modules = ['.model.entities']
    db_manager = None

    jinja_filters = {}

    _init_ran = False
    _app_instance = None

    def __init__(self, import_name=None, static_path=None, static_url_path=None,
                 static_folder='static', template_folder='templates', instance_path=None,
                 instance_relative_config=False, config_profile=None):

        # flask requires an import name, so we should too.
        if import_name is None and self.import_name is None:
            raise KegAppError('Please set the "import_name" attribute on your app class or pass it'
                              ' into the app instance.')

        # passed in value takes precedence
        import_name = import_name or self.import_name

        self.keyring_manager = None
        self.config_profile = config_profile

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

    def init(self):
        if self._init_ran:
            raise KegAppError('init() already called on this instance')
        self._init_ran = True

        self.init_config()
        self.init_logging()
        self.init_keyring()
        self.init_oath()
        self.init_error_handling()
        self.init_extensions()
        self.init_blueprints()
        self.init_filters()

        signals.app_ready.send(self)
        self._app_instance = self

        # return self for easy chaining, i.e. app = Keg().init()
        return self

    def init_config(self):
        self.config.init_app(self.config_profile, self.import_name, self.root_path)
        signals.config_ready.send(self)

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
        from keg.sqlalchemy import DatabaseManager
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

    def init_filters(self):
        self.jinja_env.filters.update(self.jinja_filters)

    def handle_server_error(self, error):
        # send_exception_email()
        return '500 SERVER ERROR<br/><br/>administrators notified'

    @classproperty
    def cli_group(cls):  # noqa
        if not hasattr(cls, '_cli_group'):
            cls._cli_group = keg.cli.init_app_cli(cls)
        return cls._cli_group

    @classmethod
    def command(cls, *args, **kwargs):
        return cls.cli_group.command(*args, **kwargs)

    @classmethod
    def cli_run(cls):
        """
            Convience function intended to be an entry point for an app's command.  Sets up the
            app and kicks off the cli command processing.
        """
        cls.cli_group()

    @classmethod
    def testing_prep(cls):
        # For now, do the import here so we don't have a hard dependency on WebTest
        from keg.testing import ContextManager
        cm = ContextManager.get_for(cls)

        # if the context manager's app isn't ready, that means this will be the first time the app
        # is instantiated.  That seems like a good indicator that tests are just beginning, so it's
        # safe to trigger the signal.  We don't want the signal to fire every time b/c
        # testing_prep() can be called more than once per test run.
        trigger_signal = not cm.is_ready()
        cm.ensure_current()

        # set a random secret key so that sessions work in tests.
        cm.app.config['SECRET_KEY'] = randchars(25)

        if trigger_signal:
            signals.testing_run_start.send(cm.app)

        return cm.app

    @classmethod
    def testing_cleanup(cls):
        # For now, do the import here so we don't have a hard dependency on WebTest
        from keg.testing import ContextManager
        cm = ContextManager.get_for(cls)
        cm.cleanup()

    def make_shell_context(self):
        return {}

    @property
    def logger(self):
        return self.logging.app_logger
