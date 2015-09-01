from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

from keg_apps import fix_sys_path
fix_sys_path()

import click

from keg.app import Keg


class CLIApp(Keg):
    import_name = __name__
    # Silence the keyring warning messages or CLI output tests get confused b/c of the warning.
    keyring_enabled = False


@CLIApp.command()
def hello():
    print('hello keg test')


@CLIApp.command()
@click.argument('name', default='foo')
def foo2(name):
    print(('hello {}'.format(name)))


@CLIApp.command('catch-error')
def catch_error():
    raise Exception('deliberate exception for testing')


if __name__ == '__main__':
    CLIApp.cli_run()
