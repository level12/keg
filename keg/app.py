from __future__ import absolute_import
from __future__ import unicode_literals

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
import warnings

import flask
from flask.config import ConfigAttribute

from keg.blueprints import keg as kegbp
import keg.cli
import keg.config
import keg.signals as signals
from keg.utils import ensure_dirs, classproperty, visit_modules
import keg.web


class KegAppError(Exception):
    pass


class Keg(flask.Flask):
    import_name = None
    use_blueprints = []
    oauth_providers = []
    keyring_enabled = ConfigAttribute('KEG_KEYRING_ENABLE')
    config_class = keg.config.Config
    keyring_manager_class = None
    sqlalchemy_enabled = False
    sqlalchemy_modules = ['.model.entities']
    jinja_filters = {}

    _init_ran = False

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
        self.init_config()
        if not self.testing:
            self.init_logging()
        self.init_keyring()
        self.init_oath()
        self.init_extensions()
        self.init_blueprints()
        self.init_error_handling()
        self.init_filters()

        signals.app_ready.send(self)
        self._init_ran = True

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
        self.init_sqlalchemy()

    def init_sqlalchemy(self):
        if self.sqlalchemy_enabled:
            from keg.sqlalchemy import db
            db.init_app(self)
            visit_modules(self.sqlalchemy_modules, self.import_name)

    def init_blueprints(self):
        self.register_blueprint(kegbp)
        for blueprint in self.use_blueprints:
            self.register_blueprint(blueprint)

    def init_logging(self):
        # adjust Flask's default logging for the application logger to not include debugging
        self.logger.handlers[0].setLevel(logging.INFO)

        #dirs_mode = self.config['KEG_DIRS_MODE']
        #ensure_dirs(Path(self.config['KEG_LOG_INFO_FPATH']).parent, dirs_mode)
        #ensure_dirs(Path(self.config['KEG_LOG_DEBUG_FPATH']).parent, dirs_mode)
        #
        #loggers = (self.logger, logging.getLogger(self.import_name))
        #file_formatter = logging.Formatter(
        #    '%(asctime)s %(levelname)s [%(name)s:%(lineno)d]: %(message)s'
        #)
        ## 10 MB
        #log_max = 1024*1024*10
        #
        #info_file_handler = RotatingFileHandler(self.config['KEG_LOG_INFO_FPATH'], log_max, 5)
        #info_file_handler.setFormatter(file_formatter)
        #info_file_handler.setLevel(logging.INFO)
        #
        #debug_file_handler = RotatingFileHandler(self.config['KEG_LOG_DEBUG_FPATH'], log_max, 5)
        #debug_file_handler.setFormatter(file_formatter)
        #debug_file_handler.setLevel(logging.DEBUG)
        #
        #for logger in loggers:
        #    logger.setLevel(logging.DEBUG)
        #    logger.addHandler(info_file_handler)
        #    logger.addHandler(debug_file_handler)

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
        #send_exception_email()
        return '500 SERVER ERROR<br/><br/>administrators notified'

    @classproperty
    def cli_group(cls):
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
    def testing_create(cls):
        app = cls(config_profile='TestProfile').init()
        app.test_request_context().push()
        signals.testing_start.send(app)

    def make_shell_context(self):
        return {}
