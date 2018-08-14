from __future__ import absolute_import
from __future__ import print_function

from keg_apps import fix_sys_path
fix_sys_path()

import click  # noqa

from keg.app import Keg  # noqa


class CLIApp(Keg):
    import_name = __name__
    # Silence the keyring warning messages or CLI output tests get confused b/c of the warning.
    keyring_enabled = False


@CLIApp.cli.command()
def hello():
    print('hello keg test')  # noqa


@CLIApp.cli.command()
@click.argument('name', default='foo')
def foo2(name):
    print((_('hello {name}', name=name)))  # noqa


@CLIApp.cli.command('catch-error')
def catch_error():
    raise Exception(_('deliberate exception for testing'))


if __name__ == '__main__':
    CLIApp.cli.main()
