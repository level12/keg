# -*- coding: utf-8 -*-
"""
    flask.run
    ~~~~~~~~~

    A simple command line application to run flask apps.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import os
import sys
from threading import Lock, Thread
from functools import update_wrapper

import click

from flask._compat import iteritems, reraise


class NoAppException(click.UsageError):
    """Raised if an application cannot be found or loaded."""


def find_best_app(module):
    """Given a module instance this tries to find the best possible
    application in the module or raises an exception.
    """
    from . import Flask

    # Search for the most common names first.
    for attr_name in 'app', 'application':
        app = getattr(module, attr_name, None)
        if app is not None and isinstance(app, Flask):
            return app

    # Otherwise find the only object that is a Flask instance.
    matches = [v for k, v in iteritems(module.__dict__)
               if isinstance(v, Flask)]

    if len(matches) == 1:
        return matches[0]
    raise NoAppException('Failed to find application in module "%s".  Are '
                         'you sure it contains a Flask application?  Maybe '
                         'you wrapped it in a WSGI middleware or you are '
                         'using a factory function.' % module.__name__)


def prepare_exec_for_file(filename):
    """Given a filename this will try to calculate the python path, add it
    to the search path and return the actual module name that is expected.
    """
    module = []

    # Chop off file extensions or package markers
    if filename.endswith('.py'):
        filename = filename[:-3]
    elif os.path.split(filename)[1] == '__init__.py':
        filename = os.path.dirname(filename)
    else:
        raise NoAppException('The file provided (%s) does exist but is not a '
                             'valid Python file.  This means that it cannot '
                             'be used as application.  Please change the '
                             'extension to .py' % filename)
    filename = os.path.realpath(filename)

    dirpath = filename
    while 1:
        dirpath, extra = os.path.split(dirpath)
        module.append(extra)
        if not os.path.isfile(os.path.join(dirpath, '__init__.py')):
            break

    sys.path.insert(0, dirpath)
    return '.'.join(module[::-1])


def locate_app(app_id):
    """Attempts to locate the application."""
    if ':' in app_id:
        module, app_obj = app_id.split(':', 1)
    else:
        module = app_id
        app_obj = None

    __import__(module)
    mod = sys.modules[module]
    if app_obj is None:
        app = find_best_app(mod)
    else:
        app = getattr(mod, app_obj, None)
        if app is None:
            raise RuntimeError('Failed to find application in module "%s"'
                               % module)

    return app


class DispatchingApp(object):
    """Special application that dispatches to a flask application which
    is imported by name in a background thread.  If an error happens
    it is is recorded and shows as part of the WSGI handling which in case
    of the Werkzeug debugger means that it shows up in the browser.
    """

    def __init__(self, loader, use_eager_loading=False):
        self.loader = loader
        self._app = None
        self._lock = Lock()
        self._bg_loading_exc_info = None
        if use_eager_loading:
            self._load_unlocked()
        else:
            self._load_in_background()

    def _load_in_background(self):
        def _load_app():
            with self._lock:
                try:
                    self._load_unlocked()
                except Exception:
                    self._bg_loading_exc_info = sys.exc_info()
        t = Thread(target=_load_app, args=())
        t.start()

    def _flush_bg_loading_exception(self):
        exc_info = self._bg_loading_exc_info
        if exc_info is not None:
            self._bg_loading_exc_info = None
            reraise(*exc_info)

    def _load_unlocked(self):
        self._app = rv = self.loader()
        self._bg_loading_exc_info = None
        return rv

    def __call__(self, environ, start_response):
        if self._app is not None:
            return self._app(environ, start_response)
        self._flush_bg_loading_exception()
        with self._lock:
            if self._app is not None:
                rv = self._app
            else:
                rv = self._load_unlocked()
            return rv(environ, start_response)


class ScriptInfo(object):
    """Help object to deal with Flask applications.  This is usually not
    necessary to interface with as it's used internally in the dispatching
    to click.
    """

    def __init__(self, app_import_path=None, debug=None, create_app=None):
        #: The application import path
        self.app_import_path = app_import_path
        #: The debug flag.  If this is not None, the application will
        #: automatically have it's debug flag overridden with this value.
        self.debug = debug
        #: Optionally a function that is passed the script info to create
        #: the instance of the application.
        self.create_app = create_app
        #: A dictionary with arbitrary data that can be associated with
        #: this script info.
        self.data = {}
        self._loaded_app = None

    def load_app(self):
        """Loads the Flask app (if not yet loaded) and returns it.  Calling
        this multiple times will just result in the already loaded app to
        be returned.
        """
        if self._loaded_app is not None:
            return self._loaded_app
        if self.create_app is not None:
            rv = self.create_app(self)
        else:
            if self.app_import_path is None:
                raise NoAppException('Could not locate Flask application. '
                                     'You did not provide FLASK_APP or the '
                                     '--app parameter.')
            rv = locate_app(self.app_import_path)
        if self.debug is not None:
            rv.debug = self.debug
        self._loaded_app = rv
        return rv


pass_script_info = click.make_pass_decorator(ScriptInfo, ensure=True)


def with_appcontext(f):
    """Wraps a callback so that it's guaranteed to be executed with the
    script's application context.  If callbacks are registered directly
    to the ``app.cli`` object then they are wrapped with this function
    by default unless it's disabled.
    """
    @click.pass_context
    def decorator(__ctx, *args, **kwargs):
        with __ctx.ensure_object(ScriptInfo).load_app().app_context():
            return __ctx.invoke(f, *args, **kwargs)
    return update_wrapper(decorator, f)


def set_debug_value(ctx, param, value):
    ctx.ensure_object(ScriptInfo).debug = value


def set_app_value(ctx, param, value):
    if value is not None:
        if os.path.isfile(value):
            value = prepare_exec_for_file(value)
        elif '.' not in sys.path:
            sys.path.insert(0, '.')
    ctx.ensure_object(ScriptInfo).app_import_path = value


debug_option = click.Option(
    ['--debug/--no-debug'],
    help='Enable or disable debug mode.',
    default=None, callback=set_debug_value)


app_option = click.Option(
    ['-a', '--app'],
    help='The application to run',
    callback=set_app_value, is_eager=True)


class AppGroup(click.Group):
    """This works similar to a regular click :class:`~click.Group` but it
    changes the behavior of the :meth:`command` decorator so that it
    automatically wraps the functions in :func:`with_appcontext`.

    Not to be confused with :class:`FlaskGroup`.
    """

    def command(self, *args, **kwargs):
        """This works exactly like the method of the same name on a regular
        :class:`click.Group` but it wraps callbacks in :func:`with_appcontext`
        unless it's disabled by passing ``with_appcontext=False``.
        """
        wrap_for_ctx = kwargs.pop('with_appcontext', True)

        def decorator(f):
            if wrap_for_ctx:
                f = with_appcontext(f)
            return click.Group.command(self, *args, **kwargs)(f)
        return decorator

    def group(self, *args, **kwargs):
        """This works exactly like the method of the same name on a regular
        :class:`click.Group` but it defaults the group class to
        :class:`AppGroup`.
        """
        kwargs.setdefault('cls', AppGroup)
        return click.Group.group(self, *args, **kwargs)


class FlaskGroup(AppGroup):
    """Special subclass of the :class:`AppGroup` group that supports
    loading more commands from the configured Flask app.  Normally a
    developer does not have to interface with this class but there are
    some very advanced use cases for which it makes sense to create an
    instance of this.

    For information as of why this is useful see :ref:`custom-scripts`.

    :param add_default_commands: if this is True then the default run and
                                 shell commands wil be added.
    :param add_app_option: adds the default :option:`--app` option.  This gets
                           automatically disabled if a `create_app`
                           callback is defined.
    :param add_debug_option: adds the default :option:`--debug` option.
    :param create_app: an optional callback that is passed the script info
                       and returns the loaded app.
    """

    def __init__(self, add_default_commands=True, add_app_option=None,
                 add_debug_option=True, create_app=None, **extra):
        params = list(extra.pop('params', None) or ())
        if add_app_option is None:
            add_app_option = create_app is None
        if add_app_option:
            params.append(app_option)
        if add_debug_option:
            params.append(debug_option)

        AppGroup.__init__(self, params=params, **extra)
        self.create_app = create_app

        if add_default_commands:
            self.add_command(run_command)
            self.add_command(shell_command)

    def get_command(self, ctx, name):
        # We load built-in commands first as these should always be the
        # same no matter what the app does.  If the app does want to
        # override this it needs to make a custom instance of this group
        # and not attach the default commands.
        #
        # This also means that the script stays functional in case the
        # application completely fails.
        rv = AppGroup.get_command(self, ctx, name)
        if rv is not None:
            return rv

        # The code below caused an exception because our app doesn't have a .cli.  Not exactly sure
        # how this was intended to be used, may be related to Flask's ability to invoke a command
        # like `flask --app=hello shell` but it doesn't seem to apply to how we do scripts in
        # Keg.

        # info = ctx.ensure_object(ScriptInfo)
        # try:
        #    app = info.load_app()
        #    print app
        #    rv = app.cli.get_command(ctx, name)
        #    if rv is not None:
        #        return rv
        # except NoAppException:
        #    pass

    def list_commands(self, ctx):
        # The commands available is the list of both the application (if
        # available) plus the builtin commands.
        rv = set(click.Group.list_commands(self, ctx))
        info = ctx.ensure_object(ScriptInfo)
        try:
            rv.update(info.load_app().cli.list_commands(ctx))
        except Exception:
            # Here we intentionally swallow all exceptions as we don't
            # want the help page to break if the app does not exist.
            # If someone attempts to use the command we try to create
            # the app again and this will give us the error.
            pass
        return sorted(rv)

    def main(self, *args, **kwargs):
        obj = kwargs.get('obj')
        if obj is None:
            obj = ScriptInfo(create_app=self.create_app)
        kwargs['obj'] = obj
        kwargs.setdefault('auto_envvar_prefix', 'FLASK')
        return AppGroup.main(self, *args, **kwargs)


def script_info_option(*args, **kwargs):
    """This decorator works exactly like :func:`click.option` but is eager
    by default and stores the value in the :attr:`ScriptInfo.data`.  This
    is useful to further customize an application factory in very complex
    situations.

    :param script_info_key: this is a mandatory keyword argument which
                            defines under which data key the value should
                            be stored.
    """
    try:
        key = kwargs.pop('script_info_key')
    except LookupError:
        raise TypeError('script_info_key not provided.')

    real_callback = kwargs.get('callback')

    def callback(ctx, param, value):
        if real_callback is not None:
            value = real_callback(ctx, value)
        ctx.ensure_object(ScriptInfo).data[key] = value
        return value

    kwargs['callback'] = callback
    kwargs.setdefault('is_eager', True)
    return click.option(*args, **kwargs)


@click.command('run', short_help='Runs a development server.')
@click.option('--host', '-h', default='127.0.0.1',
              help='The interface to bind to.')
@click.option('--port', '-p', default=5000,
              help='The port to bind to.')
@click.option('--reload/--no-reload', default=None,
              help='Enable or disable the reloader.  By default the reloader '
              'is active if debug is enabled.')
@click.option('--debugger/--no-debugger', default=None,
              help='Enable or disable the debugger.  By default the debugger '
              'is active if debug is enabled.')
@click.option('--eager-loading/--lazy-loader', default=None,
              help='Enable or disable eager loading.  By default eager '
              'loading is enabled if the reloader is disabled.')
@click.option('--with-threads/--without-threads', default=False,
              help='Enable or disable multithreading.')
@pass_script_info
def run_command(info, host, port, reload, debugger, eager_loading,
                with_threads):
    """Runs a local development server for the Flask application.

    This local server is recommended for development purposes only but it
    can also be used for simple intranet deployments.  By default it will
    not support any sort of concurrency at all to simplify debugging.  This
    can be changed with the --with-threads option which will enable basic
    multithreading.

    The reloader and debugger are by default enabled if the debug flag of
    Flask is enabled and disabled otherwise.
    """
    from werkzeug.serving import run_simple

    kegapp = info.load_app()
    if reload is None:
        reload = kegapp.debug
    if debugger is None:
        debugger = kegapp.debug
    if eager_loading is None:
        eager_loading = not reload

    app = DispatchingApp(info.load_app, use_eager_loading=eager_loading)

    # Extra startup messages.  This depends a but on Werkzeug internals to
    # not double execute when the reloader kicks in.
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # If we have an import path we can print it out now which can help
        # people understand what's being served.  If we do not have an
        # import path because the app was loaded through a callback then
        # we won't print anything.
        if info.app_import_path is not None:
            click.echo(' * Serving Flask app "%s"' % info.app_import_path)
        if info.debug is not None:
            click.echo(' * Forcing debug %s' % (info.debug and 'on' or 'off'))

    run_simple(host, port, app, use_reloader=reload,
               use_debugger=debugger, threaded=with_threads)


@click.command('shell', short_help='Runs a shell in the app context.')
@with_appcontext
def shell_command():
    """Runs an interactive Python shell in the context of a given
    Flask application.  The application will populate the default
    namespace of this shell according to it's configuration.

    This is useful for executing small snippets of management code
    without having to manually configuring the application.
    """
    import code
    from flask.globals import _app_ctx_stack
    app = _app_ctx_stack.top.app
    banner = 'Python %s on %s\nApp: %s%s\nInstance: %s' % (
        sys.version,
        sys.platform,
        app.import_name,
        app.debug and ' [debug]' or '',
        app.instance_path,
    )
    ctx = {}

    # Support the regular Python interpreter startup script if someone
    # is using it.
    startup = os.environ.get('PYTHONSTARTUP')
    if startup and os.path.isfile(startup):
        with open(startup, 'r') as f:
            eval(compile(f.read(), startup, 'exec'), ctx)

    ctx.update(app.make_shell_context())

    code.interact(banner=banner, local=ctx)


cli = FlaskGroup(help="""\
This shell command acts as general utility script for Flask applications.

It loads the application configured (either through the FLASK_APP environment
variable or the --app parameter) and then provides commands either provided
by the application or Flask itself.

The most useful commands are the "run" and "shell" command.

Example usage:

  flask --app=hello --debug run
""")


def main(as_module=False):
    this_module = __package__ + '.cli'
    args = sys.argv[1:]

    if as_module:
        if sys.version_info >= (2, 7):
            name = 'python -m ' + this_module.rsplit('.', 1)[0]
        else:
            name = 'python -m ' + this_module

        # This module is always executed as "python -m flask.run" and as such
        # we need to ensure that we restore the actual command line so that
        # the reloader can properly operate.
        sys.argv = ['-m', this_module] + sys.argv[1:]
    else:
        name = None

    cli.main(args=args, prog_name=name)


if __name__ == '__main__':
    main(as_module=True)
