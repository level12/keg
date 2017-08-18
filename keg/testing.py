from __future__ import absolute_import

import click
import click.testing
import flask
from flask_webtest import TestApp
import six

from keg import current_app
from keg.utils import app_environ_get


def _config_profile(appcls):
    config_profile = 'TestProfile'
    if appcls.import_name is not None:
        config_profile = app_environ_get(appcls.import_name, 'CONFIG_PROFILE', config_profile)
    return config_profile


class ContextManager(object):
    """
        Facilitates having a single instance of an application ready for testing.
    """
    apps = {}

    def __init__(self, appcls):
        self.appcls = appcls
        self.app = None
        self.ctx = None

    def ensure_current(self, config):

        if not self.app:
            self.app = self.appcls().init(use_test_profile=True, config=config)
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
        """
            Return the ContextManager instance for the given app class.  Only one ContextManager
            instance will be created in a Python process for any given app.
        """
        if appcls not in cls.apps:
            cls.apps[appcls] = cls(appcls)
        return cls.apps[appcls]


def invoke_command(app_cls, *args, **kwargs):
    exit_code = kwargs.pop('exit_code', 0)
    runner = kwargs.pop('runner', None) or click.testing.CliRunner()
    use_test_profile = kwargs.pop('use_test_profile', True)
    env = kwargs.pop('env', {})

    if use_test_profile:
        app_key = app_cls.environ_key('USE_TEST_PROFILE')
        env[app_key] = 'true'
    result = runner.invoke(app_cls.cli, args, env=env, catch_exceptions=False)

    # if an exception was raised, make sure you output the output to make debugging easier
    # -1 as an exit code indicates a non SystemExit exception.
    # 9/16/15: Not sure this is necessary anymore since we force catch_exceptions=False above (RLS).
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
        if cmd_name is None:
            cmd_name_args = []
        else:
            cmd_name_args = cmd_name.split(' ')
        invoke_args = cmd_name_args + list(args)
        kwargs['runner'] = self.runner

        # If the app_cls isn't set, use the class of the current app
        app_cls = self.app_cls or flask.current_app._get_current_object().__class__

        return invoke_command(app_cls, *invoke_args, **kwargs)


class WebBase(object):
    db = None
    appcls = None

    @classmethod
    def setup_class(cls):
        cls.app = cls.appcls.testing_prep()
        cls.testapp = TestApp(flask.current_app)
