from __future__ import absolute_import
from __future__ import unicode_literals

import click
import flask
import urllib

from keg._flask_cli import FlaskGroup, script_info_option, with_appcontext


class KegGroup(FlaskGroup):
    def __init__(self, add_default_commands=True, *args, **kwargs):
        FlaskGroup.__init__(self, add_default_commands, *args, **kwargs)
        if add_default_commands:
            self.add_command(routes_command)
            self.add_command(config_command)
            self.add_command(keyring_command)
            self.add_command(keyring_setup_command)


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


@click.command('config', short_help='List all configuration values.')
@with_appcontext
def config_command():
    config = flask.current_app.config
    keys = config.keys()
    keys.sort()

    for key in keys:
        click.echo('{} = {}'.format(key, config[key]))


@click.command('keyring', short_help='List keyring info')
@click.option('--unavailable', default=False, is_flag=True,
              help='Show unavailable backends with reasons.')
@with_appcontext
def keyring_command(unavailable):
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

    click.echo('Available backends (backends with priority < 1 are not'
               ' recommended and may be insecure')
    for backend in viable:
        click.echo('    {0.__module__}:{0.__name__} (priority: {1})'
                   .format(backend.__class__, backend.priority))

    click.echo('Default backend')
    backend = keyring.get_keyring()
    click.echo('    {0.__module__}:{0.__name__}'.format(backend.__class__))
    if hasattr(backend, 'file_path'):
        click.echo('    file path: {}'.format(backend.file_path))
    if not flask.current_app.keyring_manager.verify_backend():
        click.echo('WARNING: the current backend is not recommended,'
                   ' keyring substitution unavailable.')
        click.echo('\n---> You can try this app\'s keyring-setup command to fix this. <---')


@click.command('keyring-setup', short_help='Attempt to setup your virtualenv for keyring support')
@with_appcontext
def keyring_setup_command():
    flask.current_app.keyring_manager.venv_link_backend()
    click.echo('Keyring setup attempted, check log messages and the output from the keyring'
               ' command to verify status.')


def init_app_cli(appcls):
    def _create_app(script_info):
        return appcls.create_app(script_info.data['config_profile'])

    @click.group(cls=KegGroup, create_app=_create_app)
    @script_info_option('--profile', script_info_key='config_profile', default='Dev',
                        help='Name of the configuration profile to use (default: Dev).')
    def cli(**kwargs):
        pass

    return cli
