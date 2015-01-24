from __future__ import absolute_import
from __future__ import unicode_literals

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
import os.path as osp
import warnings

import appdirs
import flask
from flask.config import ConfigAttribute
from werkzeug.utils import ImportStringError

from keg.blueprints import keg as kegbp
import keg.cli
import keg.config
import keg.compat as compat
import keg.signals as signals
from keg.utils import ensure_dirs, classproperty
import keg.web


class KegError(Exception):
    pass


class Keg(flask.Flask):
    import_name = None
    use_blueprints = []
    oauth_providers = []
    keyring_enabled = ConfigAttribute('KEG_KEYRING_ENABLE')
    config_class = keg.config.Config
    keyring_manager_class = None
    sqlalchemy_enabled = False

    def __init__(self, config_profile=None, *args, **kwargs):
        if self.import_name is None:
            raise KegError('please set the import_name attribute on your app')
        if config_profile is None:
            config_profile = self.environ_get('CONFIG_PROFILE')
            if config_profile is None:
                raise KegError('The configuration profile was not passed into this Keg app and was'
                               ' also not given as an environment variable.')

        self.keyring_manager = None
        self.config_profile = config_profile

        flask.Flask.__init__(self, self.import_name, *args, **kwargs)
        self.init()

    def environ_get(self, key):
        environ_key = '{}_{}'.format(self.import_name.upper(), key.upper())
        return os.environ.get(environ_key)

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
        self.dirs = appdirs.AppDirs(self.import_name, appauthor=False, multipath=True)
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

    def _config_from_obj_location(self, obj_location):
        try:
            self.config.from_object(obj_location)
            self.configs_found.append(obj_location)
        except ImportStringError as e:
            if obj_location not in str(e):
                raise

    def init_config(self):
        profile = self.config_profile
        self.configs_found = []

        self.config['KEG_LOG_INFO_FPATH'] = osp.join(self.dirs.user_log_dir,
                                                     '{}-info.log'.format(self.import_name))
        self.config['KEG_LOG_DEBUG_FPATH'] = osp.join(self.dirs.user_log_dir,
                                                      '{}-debug.log'.format(self.import_name))

        self.default_config_objs = [
            # Keg's defaults
            'keg.config:Default',
            # Keg's defaults for the selected profile
            'keg.config:{}'.format(profile),
            # App defaults for all profiles
            '{}.config:Default'.format(self.import_name),
            # apply the profile defaults that are in the app's config file
            '{}.config:{}'.format(self.import_name, profile),
        ]
        for obj_location in self.default_config_objs:
            self._config_from_obj_location(obj_location)

        # apply settings from any of this app's configuration files
        self.possible_config_files = self.config.config_files(self)
        for fpath in self.possible_config_files:
            if osp.isfile(fpath):
                configobj = compat.object_from_source(fpath, profile)
                if configobj:
                    self.configs_found.append('{}:{}'.format(fpath, profile))
                    self.config.from_object(configobj)

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

    def init_blueprints(self):
        self.register_blueprint(kegbp)
        for blueprint in self.use_blueprints:
            self.register_blueprint(blueprint)

    def init_logging(self):
        # adjust Flask's default logging for the application logger to not include debugging
        self.logger.handlers[0].setLevel(logging.INFO)

        dirs_mode = self.config['KEG_DIRS_MODE']
        ensure_dirs(Path(self.config['KEG_LOG_INFO_FPATH']).parent, dirs_mode)
        ensure_dirs(Path(self.config['KEG_LOG_DEBUG_FPATH']).parent, dirs_mode)

        loggers = (self.logger, logging.getLogger(self.import_name))
        file_formatter = logging.Formatter(
            '%(asctime)s %(levelname)s [%(name)s:%(lineno)d]: %(message)s'
        )
        # 10 MB
        log_max = 1024*1024*10

        info_file_handler = RotatingFileHandler(self.config['KEG_LOG_INFO_FPATH'], log_max, 5)
        info_file_handler.setFormatter(file_formatter)
        info_file_handler.setLevel(logging.INFO)

        debug_file_handler = RotatingFileHandler(self.config['KEG_LOG_DEBUG_FPATH'], log_max, 5)
        debug_file_handler.setFormatter(file_formatter)
        debug_file_handler.setLevel(logging.DEBUG)

        for logger in loggers:
            logger.setLevel(logging.DEBUG)
            logger.addHandler(info_file_handler)
            logger.addHandler(debug_file_handler)

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
        pass

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
        cls.cli_group()
