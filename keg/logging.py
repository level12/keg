from __future__ import absolute_import

import datetime as dt
import logging
from logging.handlers import SysLogHandler
import os
import stat

from pythonjsonlogger import jsonlogger


log = logging.getLogger(__name__)


class Logging(object):
    stream_format_str = '%(levelname)s - %(name)s - %(message)s'
    syslog_format_str = '%(levelname)s [%(name)s:%(lineno)d]: %(message)s'
    json_format_str = '%(pathname) %(funcName) %(lineno) %(message) %(levelname)' \
                      ' %(name)s %(process) %(processName) %(message)'

    def __init__(self, config):
        self.config = config
        self.app_logger = logging.getLogger(config.app_import_name)

        self.logging_level = config.get('KEG_LOG_LEVEL', logging.INFO)
        self.logged_locations = config.get('KEG_LOG_MANAGED_LOGGERS', [None])

        self.syslog_enabled = config.get('KEG_LOG_SYSLOG_ENABLED', True)
        self.stream_enabled = config.get('KEG_LOG_STREAM_ENABLED', True)

        if 'KEG_LOG_STDOUT_FORMAT_STR' in config:
            self.stream_format_str = config['KEG_LOG_STDOUT_FORMAT_STR']

        if 'KEG_LOG_SYSLOG_FORMAT_STR' in config:
            self.syslog_format_str = config['KEG_LOG_SYSLOG_FORMAT_STR']

        if 'KEG_LOG_JSON_FORMAT_STR' in config:
            self.json_format_str = config['KEG_LOG_JSON_FORMAT_STR']

        self.syslog_format_json = config.get('KEG_LOG_SYSLOG_JSON', False)

        # Why the ".app"?  Because for a given application, you may be logging to syslog from
        # multiple locations.  For instance, uWSGI might log to syslog for this app.  In that case,
        # all the message's for the app could be namespace like:
        #  - kegdemo.app
        #  - kegdemo.uwsgi
        #  - kegdemo.uwsgi-req
        #  - kegdemo.celery
        #  - etc.
        syslog_default_ident = '{}.app'.format(config.app_import_name)
        self.syslog_ident = config.get('KEG_LOG_SYSLOG_IDENT', syslog_default_ident)

        self.auto_clear_handlers = config.get('KEG_LOG_AUTO_CLEAR_HANDLERS', True)

    def init_app(self):
        self.loggers = [logging.getLogger(location) for location in self.logged_locations]
        self.init_logger_level()
        # If we load multiple instances of the app (usually in testing) we probably don't want
        # multiple handlers created.
        if self.auto_clear_handlers:
            self.clear_keg_handlers()
        if self.stream_enabled:
            self.init_stream()
        if self.syslog_enabled:
            self.init_syslog()

    def init_logger_level(self):
        for logger in self.loggers:
            logger.setLevel(self.logging_level)

    def init_stream(self):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(self.stream_format_str))
        handler.setLevel(self.logging_level)

        self.add_handler(handler)

    def init_syslog(self):
        handler = self.create_syslog_handler()
        # A space is needed at the end of the ident so syslog recognizes it as the
        # app name and not part of the message.
        handler.ident = self.syslog_ident.rstrip() + ' '
        handler.setFormatter(self.create_syslog_formatter())
        handler.setLevel(self.logging_level)

        self.add_handler(handler)

    def add_handler(self, handler):
        for logger in self.loggers:
            handler._from_keg_logging = True
            logger.addHandler(handler)

    def clear_keg_handlers(self):
        for logger in self.loggers:
            self.clear_logger_handlers(logger)

    def clear_logger_handlers(self, logger):
        keep_handlers = []
        for handler in logger.handlers:
            if hasattr(handler, '_from_keg_logging'):
                handler.flush()
                handler.close()
            else:
                keep_handlers.append(handler)
        logger.handlers = keep_handlers

    def create_syslog_handler(self):
        kwargs = self.config.get('KEG_LOG_SYSLOG_ARGS', {})
        if 'address' not in kwargs:
            address = find_syslog_address(self.config)
            if address:
                log.debug('Using syslog address: {}'.format(address))
                kwargs['address'] = address
            else:
                log.debug('did not find syslog address')
        return SysLogHandler(**kwargs)

    def create_syslog_formatter(self):
        if self.syslog_format_json:
            return self.create_json_formatter()
        return logging.Formatter(self.syslog_format_str)

    def create_json_formatter(self):
        prefix = self.config.get('KEG_LOG_SYSLOG_JSON_PREFIX', '@cee:')
        kwargs = self.config.get('KEG_LOG_JSON_FORMATTER_KWARGS', {})
        kwargs.setdefault('prefix', prefix)
        return JSONFormatter(self.json_format_str, **kwargs)


def find_syslog_address(config):
    if _is_socket('/var/run/syslog'):
        return '/var/run/syslog'
    if _is_socket('/dev/log'):
        return '/dev/log'


def _is_socket(path):
    if not os.path.exists(path):
        return False
    mode = os.stat(path).st_mode
    return stat.S_ISSOCK(mode)


class JSONFormatter(jsonlogger.JsonFormatter):
    def process_log_record(self, log_record):
        # Log processing providers like logzio often auto-recognize a field labeled "timestamp".
        log_record['timestamp'] = dt.datetime.utcnow().isoformat()
        return log_record
