from __future__ import absolute_import
from __future__ import unicode_literals

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os.path as osp

import appdirs
import flask
from werkzeug.utils import ImportStringError

import keg.blueprint
import keg.cli
import keg.config
import keg.compat as compat
from keg.utils import ensure_dirs


class KegError(Exception):
    pass


class Keg(flask.Flask):
    import_name = None
    use_blueprints = []

    @classmethod
    def create_app(cls, config_profile, *args, **kwargs):
        if cls.import_name is None:
            raise KegError('please set the import_name attribute on your app')
        app = cls(cls.import_name, *args, **kwargs)
        app.init(config_profile)
        return app

    def init(self, config_profile):
        self.dirs = appdirs.AppDirs(self.import_name, appauthor=False, multipath=True)
        self.init_config(config_profile)
        self.init_blueprints()
        if not self.testing:
            self.init_logging()

    def _config_from_obj_location(self, obj_location):
        try:
            self.config.from_object(obj_location)
        except ImportStringError as e:
            if obj_location not in str(e):
                raise

    def init_config(self, profile):

        self.config['KEG_LOG_INFO_FPATH'] = osp.join(self.dirs.user_log_dir,
                                                     '{}-info.log'.format(self.import_name))
        self.config['KEG_LOG_DEBUG_FPATH'] = osp.join(self.dirs.user_log_dir,
                                                      '{}-debug.log'.format(self.import_name))

        # lock it down by default
        self.config['KEG_DIRS_MODE'] = 0o700

        possible_config_objs = [
            # Keg's defaults for the selected profile
            'keg.config:{}'.format(profile),
            # App defaults for all profiles
            '{}.config:Default'.format(self.import_name),
            # apply the profile defaults that are in the app's config file
            '{}.config:{}'.format(self.import_name, profile),
        ]
        for obj_location in possible_config_objs:
            self._config_from_obj_location(obj_location)

        # apply settings from any of this app's configuration files
        for fpath in keg.config.config_files(self):
            if osp.isfile(fpath):
                configobj = compat.object_from_source(fpath, profile)
                if configobj:
                    self.config.from_object(configobj)

    def init_blueprints(self):
        self.register_blueprint(keg.blueprint.keg)
        for blueprint in self.use_blueprints:
            self.register_blueprint(blueprint)

    def init_logging(self):
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
            logger.handlers = []
            logger.addHandler(info_file_handler)
            logger.addHandler(debug_file_handler)

    def init_error_handling(self):
        # handle status codes
        generic_errors = range(500, 506)
        for err in generic_errors:
            self.errorhandler(err)(self.handle_server_error)

    def handle_server_error(self, error):
        #shousend_exception_email()
        return '500 SERVER ERROR<br/><br/>administrators notified'

    @classmethod
    def command(cls, *args, **kwargs):
        if not hasattr(cls, '_cli_group'):
            cls._cli_group = keg.cli.init_app_cli(cls)
        return cls._cli_group.command(*args, **kwargs)

    @classmethod
    def runcli(cls):
        if not hasattr(cls, '_cli_group'):
            cls._cli_group = keg.cli.init_app_cli(cls)

        cls._cli_group()
