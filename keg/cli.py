from __future__ import absolute_import
from __future__ import unicode_literals

import click
import flask
import urllib

from keg._flask_cli import FlaskGroup, script_info_option, with_appcontext
from keg.keyring import keyring as keg_keyring


class KegGroup(FlaskGroup):
    def __init__(self, add_default_commands=True, *args, **kwargs):
        FlaskGroup.__init__(self, add_default_commands, *args, **kwargs)
        if add_default_commands:
            self.add_command(routes_command)
            self.add_command(config_command)
            self.add_command(keyring_group)


@click.command('routes', short_help='List the routes defined for this app.')
@with_appcontext
def routes_command():
    output = []
    endpoint_len = 0
    methods_len = 0

    for rule in flask.current_app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        endpoint_len = max(endpoint_len, len(rule.endpoint))
        methods_len = max(methods_len, len(methods))

    for rule in flask.current_app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.unquote("{}   {}   {}".format(
            rule.endpoint.ljust(endpoint_len), methods.ljust(methods_len), rule))
        output.append(line)

    for line in sorted(output):
        click.echo(line)


@click.command('config', short_help='List diagnostic info related to config files, profiles, and'
                                    ' values.')
@with_appcontext
def config_command():
    app = flask.current_app
    config = app.config
    keys = config.keys()
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
        if name == 'setup':
            return keyring_setup
        if name == 'delete':
            return keyring_delete


def keyring_notify_no_module():
    click.echo('Keyring module not installed. Keyring functionality disabled.\n\nYou can'
               ' enable keyring functionality by installing the package:'
               ' `pip install keyring`.')


@click.command('keyring', cls=KeyringGroup, invoke_without_command=True,
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
        click.echo('\nWARNING: the current backend is not recommended,'
                   ' keyring substitution unavailable.')
        click.echo('\n---> You can try this app\'s `keyring setup` command to fix this. <---')


@click.command('setup', short_help='Attempt to setup your virtualenv for keyring support.')
@with_appcontext
def keyring_setup():
    flask.current_app.keyring_manager.venv_link_backend()
    click.echo('Keyring setup attempted, check log messages and the output from the keyring'
               ' status command to verify.')


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
        app = appcls(config_profile=script_info.data['config_profile'])
        app.init()
        return app

    @click.group(cls=KegGroup, create_app=_create_app)
    @script_info_option('--profile', script_info_key='config_profile', default=None,
                        help='Name of the configuration profile to use.')
    def cli(**kwargs):
        pass

    return cli
