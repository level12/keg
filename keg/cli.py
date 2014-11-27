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
        print(line)


def init_app_cli(appcls):
    def _create_app(script_info):
        return appcls.create_app(script_info.data['config_profile'])

    @click.group(cls=KegGroup, create_app=_create_app)
    @script_info_option('--profile', script_info_key='config_profile', default='Dev',
                        help='Name of the configuration profile to use (default: Dev).')
    def cli(**kwargs):
        pass

    return cli
