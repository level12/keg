from __future__ import absolute_import
from __future__ import unicode_literals

import logging
from logging.handlers import RotatingFileHandler
import os.path as osp

from keg.utils import ensure_dirs


class Logging(object):
    file_formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s:%(lineno)d]: %(message)s'
    )

    def __init__(self, config):
        self.config = config
        self.log_dpath = self.config['KEG_LOG_DPATH']
        self.log_fname = self.config['KEG_LOG_FNAME']
        self.logger = None

    def log_fpath(self):
        return osp.join(self.log_dpath, self.log_fname)

    def init_main_log(self):
        log_fpath = self.log_fpath()

        dir_mode = self.config['KEG_DIR_MODE']
        ensure_dirs(self.log_dpath, mode=dir_mode)

        log_max = self.config['KEG_LOG_MAX_BYTES']
        log_backups = self.config['KEG_LOG_MAX_BACKUPS']

        file_handler = RotatingFileHandler(log_fpath, maxBytes=log_max, backupCount=log_backups,
                                           encoding='utf-8')
        file_handler.setFormatter(self.file_formatter)
        file_handler.setLevel(logging.WARN)

        logger = logging.getLogger(self.config.app_import_name)
        logger.addHandler(file_handler)
        logger.setLevel(logging.WARN)

        self.logger = logger

    def init_app(self):
        self.init_main_log()
