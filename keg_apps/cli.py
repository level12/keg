from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

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
