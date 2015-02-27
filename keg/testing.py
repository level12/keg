from __future__ import absolute_import
from __future__ import unicode_literals

import sys

import click
import click.testing
import flask
from flask.ext.webtest import TestApp

from keg import current_app


class ContextManager(object):
    apps = {}

    def __init__(self, appcls):
        self.appcls = appcls
        self.app = None
        self.ctx = None

    def ensure_current(self):
        if not self.app:
            self.app = app = self.appcls(config_profile='TestProfile').init()
            self.ctx = app.app_context()
            self.ctx.push()

        if current_app is not self.app:
            self.ctx.push()

        return app

    def cleanup(self):
        self.ctx.pop()

    def is_ready(self):
        return self.app is not None

    @classmethod
    def get_for(cls, appcls):
        if appcls not in cls.apps:
            cls.apps[appcls] = cls(appcls)
        return cls.apps[appcls]


class CLIBase(object):
    # child classes will need to set these values in order to use the class
    app_cls = None
    cmd_name = None

    @classmethod
    def setup_class(cls):
        cls.runner = click.testing.CliRunner()

    def invoke(self, *args, **kwargs):
        exit_code = kwargs.pop('exit_code', 0)
        cmd_name = kwargs.pop('cmd_name', self.cmd_name)

        result = self.runner.invoke(
            self.app_cls.cli_group,
            [cmd_name] + list(args),
            catch_exceptions=False,
        )

        # if an exception was raised, make sure you output the output to make debugging easier
        # -1 as an exit code indicates a non SystemExit exception.
        if result.exit_code == -1:
            print result.output
            raise result.exc_info[1], None, result.exc_info[2]

        error_message = 'Command exit code {}, expected {}.  Result output follows:\n{}'
        assert result.exit_code == exit_code, error_message.format(result.exit_code, exit_code,
                                                                   result.output)
        return result


class WebBase(object):
    db = None
    appcls = None

    @classmethod
    def setup_class(cls):
        cls.appcls.testing_prep()
        cls.app = flask.current_app
        cls.testapp = TestApp(flask.current_app)

    @classmethod
    def teardown_class(cls):
        cls.app = None
        cls.appcls.testing_cleanup()
