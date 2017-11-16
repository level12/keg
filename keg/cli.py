from __future__ import absolute_import

from collections import defaultdict
import platform

import click
import flask
import flask.cli
from six.moves import urllib

from keg import current_app
from keg.keyring import keyring as keg_keyring


class KegAppGroup(flask.cli.AppGroup):
    def __init__(self, create_app, add_default_commands=True, *args, **kwargs):
        self.create_app = create_app

        flask.cli.AppGroup.__init__(self, *args, **kwargs)
        if add_default_commands:
            self.add_command(dev_command)

        self._loaded_plugin_commands = False

    def _load_plugin_commands(self):
        if self._loaded_plugin_commands:
            return
        try:
            import pkg_resources
        except ImportError:
            self._loaded_plugin_commands = True
            return

        for ep in pkg_resources.iter_entry_points('flask.commands'):
            self.add_command(ep.load(), ep.name)
        for ep in pkg_resources.iter_entry_points('keg.commands'):
            self.add_command(ep.load(), ep.name)
        self._loaded_plugin_commands = True

    def list_commands(self, ctx):
        self._load_plugin_commands()

        info = ctx.ensure_object(flask.cli.ScriptInfo)
        info.load_app()
        rv = set(click.Group.list_commands(self, ctx))
        return sorted(rv)

    def get_command(self, ctx, name):
        info = ctx.ensure_object(flask.cli.ScriptInfo)
        info.load_app()
        return click.Group.get_command(self, ctx, name)

    def main(self, *args, **kwargs):
        obj = kwargs.get('obj')
        if obj is None:
            obj = flask.cli.ScriptInfo(create_app=self.create_app)
        kwargs['obj'] = obj
        # TODO: figure out if we want to use this next line.
        #kwargs.setdefault('auto_envvar_prefix', 'FLASK')
        return flask.cli.AppGroup.main(self, *args, **kwargs)


@click.group('develop', help='Developer info and utils.')
def dev_command():
    pass


dev_command.add_command(flask.cli.run_command)
dev_command.add_command(flask.cli.shell_command)


@dev_command.command('routes', short_help='List the routes defined for this app.')
@flask.cli.with_appcontext
def routes_command():
    output = []
    endpoint_len = 0
    methods_len = 0

    # calculate how wide the output columns need to be
    for rule in flask.current_app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        endpoint_len = max(endpoint_len, len(rule.endpoint))
        methods_len = max(methods_len, len(methods))

    # generate the output
    for rule in flask.current_app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.parse.unquote("{}   {}   {}".format(
            rule.endpoint.ljust(endpoint_len), methods.ljust(methods_len), rule))
        output.append(line)

    for line in sorted(output):
        click.echo(line)


@dev_command.command('templates', short_help='Show paths searched for a template.')
@flask.cli.with_appcontext
def templates_command():
    jinja_loader = flask.current_app.jinja_env.loader
    paths = defaultdict(list)
    for template in jinja_loader.list_templates():
        for loader, template in jinja_loader._iter_loaders(template):
            for dpath in loader.searchpath:
                paths[dpath].append(template)
    for dpath in sorted(paths.keys()):
        template_paths = sorted(paths[dpath])
        click.echo(dpath)
        for tpath in template_paths:
            click.echo('    {}'.format(tpath))


@dev_command.command('config', short_help='List info related to config files, profiles, and'
                     ' values.')
@flask.cli.with_appcontext
def config_command():
    app = flask.current_app
    config = app.config
    keys = list(config.keys())
    keys.sort()

    click.echo('Default config objects:')
    for val in config.default_config_locations_parsed():
        click.echo('    {}'.format(val))

    click.echo('Config file locations:')
    for val in config.config_file_paths():
        click.echo('    {}'.format(val))

    click.echo('Config objects used:')
    for val in config.configs_found:
        click.echo('    {}'.format(val))

    click.echo('Resulting app config (including Flask defaults):')
    for key in keys:
        click.echo('    {} = {}'.format(key, config[key]))


class DatabaseGroup(click.MultiCommand):

    def list_commands(self, ctx):
        return ['clear', 'init']

    def get_command(self, ctx, name):
        if name == 'init':
            return database_init
        if name == 'clear':
            return database_clear


@dev_command.command('db', cls=DatabaseGroup, invoke_without_command=True,
                     help='Lists database related sub-commands.')
@flask.cli.with_appcontext
@click.pass_context
def database_group(ctx):
    # only take action if no subcommand is involved.
    if ctx.invoked_subcommand is None:
        if not current_app.db_enabled:
            click.echo('Database not enabled for this app.  No subcommands available.')
        else:
            # Database enabled, but no subcommand was given, therefore we want to just show
            # the help message, which would be the default behavior if we had not used the
            # invoke_Without_command option.
            click.echo(ctx.get_help())
            ctx.exit()


@click.command('init', short_help='Create all db objects, send related events.')
@click.option('--clear-first', default=False, is_flag=True,
              help='Clear DB of all data and drop all objects before init.')
@flask.cli.with_appcontext
def database_init(clear_first):
    if clear_first:
        current_app.db_manager.db_init_with_clear()
        click.echo('Database cleared and initialized')
    else:
        current_app.db_manager.db_init()
        click.echo('Database initialzed')


@click.command('clear', short_help='Clear DB of all data and drop all objects.')
@flask.cli.with_appcontext
def database_clear():
    current_app.db_manager.db_clear()
    click.echo('Database cleared')


class KeyringGroup(click.MultiCommand):

    def list_commands(self, ctx):
        if keg_keyring:
            return ['delete', 'list-keys', 'setup', 'status']
        else:
            return ['status']

    def get_command(self, ctx, name):
        if name == 'status':
            return keyring_status
        if name == 'list-keys':
            return keyring_list_keys
        if name == 'delete':
            return keyring_delete


def keyring_notify_no_module():
    click.echo('Keyring module not installed. Keyring functionality disabled.\n\nYou can'
               ' enable keyring functionality by installing the package:'
               ' `pip install keyring`.')


@dev_command.command('keyring', cls=KeyringGroup, invoke_without_command=True,
                     help='Lists keyring related sub-commands.')
@click.pass_context
def keyring_group(ctx):
    # only take action if no subcommand is involved.
    if ctx.invoked_subcommand is None:
        if keg_keyring is None:
            keyring_notify_no_module()
        else:
            # keyring is available, but no subcommand was given, therefore we want to just show
            # the help message, which would be the default behavior if we had not used the
            # invoke_Without_command option.
            click.echo(ctx.get_help())
            ctx.exit()


@click.command('status', short_help='Show keyring related status info.')
@click.option('--unavailable', default=False, is_flag=True,
              help='Show unavailable backends with reasons.')
@flask.cli.with_appcontext
def keyring_status(unavailable):
    if keg_keyring is None:
        keyring_notify_no_module()
        return
    import keyring
    import keyring.backend as kb
    viable = kb.get_all_keyring()

    # call get_all_keyring() before this so we are sure all keyrings are loaded
    # on KeyringBackend
    if unavailable:
        click.echo('Unavailable backends')
        for cls in kb.KeyringBackend._classes:
            try:
                cls.priority
            except Exception as e:
                click.echo('    {0.__module__}:{0.__name__} - {1}'.format(cls, e))

    click.echo('\nAvailable backends (backends with priority < 1 are not'
               ' recommended and may be insecure)')
    for backend in viable:
        click.echo('    {0.__module__}:{0.__name__} (priority: {1})'
                   .format(backend.__class__, backend.priority))

    click.echo('\nDefault backend')
    backend = keyring.get_keyring()
    click.echo('    {0.__module__}:{0.__name__}'.format(backend.__class__))
    if hasattr(backend, 'file_path'):
        click.echo('    file path: {}'.format(backend.file_path))

    if not flask.current_app.keyring_enabled:
        click.echo('\nKeyring functionality for this app has been DISABLED through the config'
                   ' setting KEG_KEYRING_ENABLE.')
    elif not flask.current_app.keyring_manager.verify_backend():
        click.echo('\nWARNING: the current backend is insecure,'
                   ' keyring substitution unavailable.')
        if platform.system() == 'Linux':
            click.echo('\nTRY THIS: use the SecretStorage Setup utility to get a more secure'
                       ' keyring backend.')
            click.echo('https://pypi.python.org/pypi/SecretStorage-Setup\n')


@click.command('list-keys', short_help='Show all keys used in config value substitution.')
@flask.cli.with_appcontext
def keyring_list_keys():
    km = flask.current_app.keyring_manager
    for key in sorted(km.sub_keys_seen):
        click.echo(key)


@click.command('delete', short_help='Delete an entry from the keyring.')
@click.argument('key')
@flask.cli.with_appcontext
def keyring_delete(key):
    flask.current_app.keyring_manager.delete(key)


class CLILoader(object):
    """
        This loader takes care of the complexity of click object setup and instantiation in the
        correct order so that application level CLI options are available before the Keg app is
        instantiated (so the options can be used to configure the app).

        The order of events is:

        - instantiate KegAppGroup
        - KegAppGroup.main() is called
            1. the ScriptInfo object is instantiated
            2. normal click behavior starts, including argument parsing
                - arguments are always parsed due to invoke_without_command=True
            3. during argument parsing, option callbacks are excuted which will result in at least
               the profile name being saved in ScriptInfo().data
            4. Normal click .main() behavior will continue which could include processing commands
               decorated with flask.cli.with_appcontext() or calls to KegAppGroup.list_commands()
               or KegAppGroup.get_command().
                - ScriptInfo.init_app() will be called during any of these operations
                - ScriptInfo.init_app() will call self.create_app() below with the ScriptInfo
                  instance
    """
    def __init__(self, appcls):
        self.appcls = appcls
        # Don't store instance-level vars here.  This object is only instantiated once per Keg
        # sub-class but can be used across multiple app instance creations.  So, anything app
        # instance specific should go on the ScriptInfo instance (see self.options_callback()).

    def create_group(self):
        """ Create the top most click Group instance which is the entry point for any Keg app
            being called in a CLI context.

            The return value of this context gets set on Keg.cli
        """

        return KegAppGroup(
            self.create_app,
            params=self.create_script_options(),
            callback=self.main_callback,
            invoke_without_command=True,
        )

    def create_app(self, script_info):
        """ Instantiate our app, sending CLI option values through as needed. """
        init_kwargs = self.option_processor(script_info.data)
        return self.appcls().init(**init_kwargs)

    def option_processor(self, cli_options):
        """
            Turn cli_options, which is the result of all parsed options in create_script_options()
            into a dict which will be given as kwargs to the app's .init() method.
        """
        retval = dict(config_profile=cli_options.get('profile', None), config={})
        if cli_options.get('quiet', False):
            retval['config']['KEG_LOG_STREAM_ENABLED'] = False
        return retval

    def create_script_options(self):
        """ Create app level options, ideally that are used to configure the app itself.  """
        return [
            click.Option(['--profile'], is_eager=True, default=None, callback=self.options_callback,
                         help='Name of the configuration profile to use.'),
            click.Option(['--quiet'], is_eager=True, is_flag=True, default=False,
                         callback=self.options_callback,
                         help='Set default logging level to logging.WARNING.')
        ]

    def options_callback(self, ctx, param, value):
        """ This method is called after argument parsing, after ScriptInfo instantiation but before
            create_app() is called.  It's the only way to get the options into ScriptInfo.data
            before the Keg app instance is instantiated.
        """
        si = ctx.ensure_object(flask.cli.ScriptInfo)
        si.data[param.name] = value

    def main_callback(self, **kwargs):
        """
            Default Click behavior is to call the help method if no arguments are given to the
            top-most command.  That's good UX, but the way Click impliments it, the help is
            shown before argument parsing takes place.  That's bad, because it means our
            options_callback() is never called and the config profile isn't available when the
            help command calls KegAppGroup.list_commands().

            So, we force Click to always parse the args using `invoke_without_command=True` above,
            but when we do that, Click turns off the automatic display of help.  So, we just
            impliment help-like behavior in this method, which gives us the same net result
            as default Click behavior.
        """
        ctx = click.get_current_context()

        if ctx.invoked_subcommand is not None:
            # A subcommand is present, so arguments were passed.
            return

        click.echo(ctx.get_help(), color=ctx.color)
        ctx.exit()
