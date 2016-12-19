from __future__ import absolute_import

import pathlib

from keg_apps.logging import LoggingApp, log
from keg import signals


class TestLogging(object):

    def test_default_log_file(self, tmpdir):
        tmpdir = str(tmpdir)

        @signals.config_ready.connect
        def apply_config(app):
            app.config['KEG_LOG_DPATH'] = tmpdir

        app = LoggingApp().init()
        log.warning('test warn log')
        log.info('test info log')

        log_fpath = pathlib.Path(app.logging.log_fpath())
        with log_fpath.open('r', encoding='utf-8') as fh:
            contents = fh.read()

        assert 'test warn log' in contents
        assert 'test info log' not in contents
