from __future__ import absolute_import

import contextlib

import click
import click.testing
import flask
import six
from flask_webtest import TestApp
from werkzeug.datastructures import ImmutableMultiDict, MultiDict

from keg import current_app, signals
from keg.utils import app_environ_get


def _config_profile(appcls):
    config_profile = 'TestProfile'
    if appcls.import_name is not None:
        config_profile = app_environ_get(appcls.import_name, 'CONFIG_PROFILE', config_profile)
    return config_profile


class ContextManager(object):
    """
        Facilitates having a single instance of an application ready for testing.

        By default, this is used in ``Keg.testing_prep``.

        Constructor arg is the Keg app class to manage for tests.
    """
    apps = {}

    def __init__(self, appcls):
        self.appcls = appcls
        self.app = None
        self.ctx = None

    def ensure_current(self, config):
        """Ensure the manager's app has an instance set as flask's ``current_app``"""

        if not self.app:
            self.app = self.appcls().init(use_test_profile=True, config=config)
            self.ctx = self.app.app_context()
            self.ctx.push()

        if current_app._get_current_object is not self.app:
            self.ctx.push()

        return self.app

    def cleanup(self):
        """Pop the app context"""
        self.ctx.pop()

    def is_ready(self):
        """Indicates the manager's app instance exists.

        The instance should be created with ``get_for``. Only one ContextManager instance will get
        created in a Python process for any given app. But, ``get_for`` may be called multiple
        times. The first call to ``ensure_current`` will set up the application and bring the
        manager to a ready state."""
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


@contextlib.contextmanager
def app_config(**kwargs):
    """
        Set config values on any apps instantiated while the context manager is active.
        This is intended to be used with cli tests where the ``current_app`` in the test will be
        different from the ``current_app`` when the CLI command is invoked, making it very difficult
        to dynamically set app config variables using mock.patch.dict like we normally would.

        Example::

            class TestCLI(CLIBase):
                app_cls = MyApp
                def test_it(self):
                    with testing.app_config(FOO_NAME='Bar'):
                        result = self.invoke('echo-foo-name')
                    assert 'Bar' in result.output
    """
    @signals.config_complete.connect
    def set_config(app):
        app.config.update(kwargs)

    yield


@contextlib.contextmanager
def inrequest(*req_args, args_modifier=None, **req_kwargs):
    """A decorator/context manager to add the flask request context to a test function.

    Allows test to assume a request context without running a full view stack. Use for
    unit-testing a view instance without setting up a webtest instance for the app and
    running requests.

    Flask's ``request.args`` is normally immutable, but in test cases, it can be helpful to
    patch in args without needing to construct the URL. But, we don't want to leave them
    mutable, because potential app bugs could be masked in doing so. To modify args, pass
    in a callable as ``args_modifier`` that takes the args dict to be modified in-place. Args
    will only be mutable for executing the modifier, then returned to immutable for the
    remainder of the scope.

    Assumes that ``flask.current_app`` is pointing to the desired app.

    Example::

        @inrequest('/mypath?foo=bar&baz=boo')
        def test_in_request_args(self):
            assert flask.request.args['foo'] == 'bar'

        def test_request_args_mutated(self):
            def args_modifier(args_dict):
                args_dict['baz'] = 'custom-value'

            with inrequest('/mypath?foo=bar&baz=boo', args_modifier=args_modifier):
                assert flask.request.args['foo'] == 'bar'
                assert flask.request.args['baz'] == 'custom-value'
    """
    with flask.current_app.test_request_context(*req_args, **req_kwargs):
        if callable(args_modifier):
            # Temporarily turn args into a mutable MultiDict to be patched. Then, we must
            # be sure to turn them back immutable, or else tests may end up not catching
            # bugs that attempt to modify request args improperly.
            new_args = MultiDict(flask.request.args)
            args_modifier(new_args)
            flask.request.args = ImmutableMultiDict(new_args)

        yield


def invoke_command(app_cls, *args, **kwargs):
    """Invoke a command using a CLI runner and return the result.

    Optional kwargs:
    - exit_code: Default 0. Process exit code to assert.
    - runner: Default ``click.testing.CliRunner()``. CLI runner instance to use for invocation.
    - use_test_profile: Default True. Drive invoked app to use test profile instead of default.
    """
    exit_code = kwargs.pop('exit_code', 0)
    runner = kwargs.pop('runner', None) or click.testing.CliRunner()
    use_test_profile = kwargs.pop('use_test_profile', True)
    env = kwargs.pop('env', {})

    if use_test_profile:
        app_key = app_cls.environ_key('USE_TEST_PROFILE')
        env[app_key] = 'true'
    result = runner.invoke(app_cls.cli, args, env=env, catch_exceptions=False, **kwargs)

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
    """Test class base for testing Keg click commands.

    Creates a CLI runner instance, and allows subclass to call ``self.invoke`` with
    command args.

    Class attributes:
    - app_cls: Optional, will default to ``flask.current_app`` class.
    - cmd_name: Optional, provides default in ``self.invoke`` for ``cmd_name`` kwarg.
    """
    # child classes will need to set these values in order to use the class
    app_cls = None
    cmd_name = None

    @classmethod
    def setup_class(cls):
        cls.runner = click.testing.CliRunner()

    def invoke(self, *args, **kwargs):
        """Run a command, perform some assertions, and return the result for testing."""
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
