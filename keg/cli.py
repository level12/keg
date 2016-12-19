from __future__ import absolute_import

from collections import defaultdict
import platform

import click
import flask
from six.moves import urllib

from keg import current_app
from keg._flask_cli import FlaskGroup, script_info_option, with_appcontext, run_command, \
    shell_command
from keg.keyring import keyring as keg_keyring


class KegGroup(FlaskGroup):
    def __init__(self, add_default_commands=True, *args, **kwargs):
        FlaskGroup.__init__(self, add_default_commands=False, *args, **kwargs)
        if add_default_commands:
            self.add_command(dev_command)


@click.group('develop', help='Developer info and utils.')
def dev_command():
    pass

dev_command.add_command(run_command)
dev_command.add_command(shell_command)


@dev_command.command('routes', short_help='List the routes defined for this app.')
@with_appcontext
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
@with_appcontext
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
@with_appcontext
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
@with_appcontext
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
@with_appcontext
def database_init(clear_first):
    if clear_first:
        current_app.db_manager.db_init_with_clear()
        click.echo('Database cleared and initialized')
    else:
        current_app.db_manager.db_init()
        click.echo('Database initialzed')


@click.command('clear', short_help='Clear DB of all data and drop all objects.')
@with_appcontext
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
@with_appcontext
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
@with_appcontext
def keyring_list_keys():
    km = flask.current_app.keyring_manager
    for key in sorted(km.sub_keys_seen):
        click.echo(key)


@click.command('delete', short_help='Delete an entry from the keyring.')
@click.argument('key')
@with_appcontext
def keyring_delete(key):
    flask.current_app.keyring_manager.delete(key)


def init_app_cli(appcls):

    # this function will be used to initialize the app along, including the value of config_profile
    # which can be passed on the command line.
    def _create_app(script_info):
        app = appcls()
        app.init(config_profile=script_info.data['config_profile'])
        return app

    @click.group(cls=KegGroup, create_app=_create_app)
    @script_info_option('--profile', script_info_key='config_profile', default=None,
                        help='Name of the configuration profile to use.')
    def cli(**kwargs):
        pass

    return cli
