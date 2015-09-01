from __future__ import absolute_import
from __future__ import unicode_literals

import os

import click
import click.testing
import flask
from flask.ext.webtest import TestApp
import six

from keg import current_app
from keg.utils import app_environ_get


def _config_profile(appcls):
    config_profile = 'TestProfile'
    if appcls.import_name is not None:
        config_profile = app_environ_get(appcls.import_name, 'CONFIG_PROFILE', config_profile)
    return config_profile


class ContextManager(object):
    apps = {}

    def __init__(self, appcls):
        self.appcls = appcls
        self.app = None
        self.ctx = None

    def ensure_current(self):

        if not self.app:
            self.app = self.appcls(config_profile=_config_profile(self.appcls))
            self.app.init()
            self.ctx = self.app.app_context()
            self.ctx.push()

        if current_app._get_current_object is not self.app:
            self.ctx.push()

        return self.app

    def cleanup(self):
        self.ctx.pop()

    def is_ready(self):
        return self.app is not None

    @classmethod
    def get_for(cls, appcls):
        key = '{}-{}'.format(appcls, _config_profile(appcls))
        if key not in cls.apps:
            cls.apps[key] = cls(appcls)
        return cls.apps[key]


def invoke_command(app_cls, *args, **kwargs):
    exit_code = kwargs.pop('exit_code', 0)
    runner = kwargs.pop('runner', click.testing.CliRunner())

    result = runner.invoke(app_cls.cli_group, args, catch_exceptions=False)

    # if an exception was raised, make sure you output the output to make debugging easier
    # -1 as an exit code indicates a non SystemExit exception.
    if result.exit_code == -1:
        click.echo(result.output)
        six.reraise(result.exc_info[1], None, result.exc_info[2])

    error_message = 'Command exit code {}, expected {}.  Result output follows:\n{}'
    assert result.exit_code == exit_code, error_message.format(result.exit_code, exit_code,
                                                               result.output)
    return result


class CLIBase(object):
    # child classes will need to set these values in order to use the class
    app_cls = None
    cmd_name = None

    @classmethod
    def setup_class(cls):
        cls.runner = click.testing.CliRunner()

    def invoke(self, *args, **kwargs):
        cmd_name = kwargs.pop('cmd_name', self.cmd_name)
        invoke_args = cmd_name.split(' ') + list(args)
        kwargs['runner'] = self.runner
        return invoke_command(self.app_cls, *invoke_args, **kwargs)
        #exit_code = kwargs.pop('exit_code', 0)
        #
        #
        #result = self.runner.invoke(
        #    self.app_cls.cli_group,
        #    ,
        #    catch_exceptions=False,
        #)
        #
        ## if an exception was raised, make sure you output the output to make debugging easier
        ## -1 as an exit code indicates a non SystemExit exception.
        #if result.exit_code == -1:
        #    click.echo(result.output)
        #    six.reraise(result.exc_info[1], None, result.exc_info[2])
        #
        #error_message = 'Command exit code {}, expected {}.  Result output follows:\n{}'
        #assert result.exit_code == exit_code, error_message.format(result.exit_code, exit_code,
        #                                                           result.output)
        #return result


class WebBase(object):
    db = None
    appcls = None

    @classmethod
    def setup_class(cls):
        cls.appcls.testing_prep()
        cls.app = flask.current_app
        cls.testapp = TestApp(flask.current_app)
