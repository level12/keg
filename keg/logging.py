from __future__ import absolute_import

import logging
from logging.handlers import RotatingFileHandler
import os.path as osp

from keg.utils import ensure_dirs


class Logging(object):

    def __init__(self, config):
        self.config = config
        self.log_dpath = self.config['KEG_LOG_DPATH']
        self.log_fname = self.config['KEG_LOG_FNAME']
        self.file_format_str = self.config['KEG_LOG_FILE_FORMAT_STR']
        self.stdout_format_str = self.config['KEG_LOG_STDOUT_FORMAT_STR']

        self.loggers = [logging.getLogger(location) for location in self.logged_locations]
        self.app_logger = logging.getLogger(self.config.app_import_name)

    @property
    def logged_locations(self):
        # todo: could probably make this configurable
        return [
            self.config.app_import_name,
            'keg',
        ]

    def init_logger_level(self):
        for logger in self.loggers:
            # Our stdout logger uses INFO, so make that the level we log at.  The handler levels
            # on the file logger will keep INFO messages out of the log file.
            # If we ever impliment a debug or verbose flag on the command line, we'll have to adjust
            # this accordingly.
            logger.setLevel(logging.INFO)

    def log_fpath(self):
        return osp.join(self.log_dpath, self.log_fname)

    def init_main_log(self):
        log_fpath = self.log_fpath()
        file_formatter = logging.Formatter(self.file_format_str)

        dir_mode = self.config['KEG_DIR_MODE']
        ensure_dirs(self.log_dpath, mode=dir_mode)

        log_max = self.config['KEG_LOG_MAX_BYTES']
        log_backups = self.config['KEG_LOG_MAX_BACKUPS']

        file_handler = RotatingFileHandler(log_fpath, maxBytes=log_max, backupCount=log_backups,
                                           encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.WARN)

        for logger in self.loggers:
            logger.addHandler(file_handler)

    def init_stdout_log(self):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(self.stdout_format_str))
        handler.setLevel(logging.INFO)

        for logger in self.loggers:
            logger.addHandler(handler)

    def init_app(self):
        self.init_logger_level()
        self.init_main_log()
        self.init_stdout_log()
