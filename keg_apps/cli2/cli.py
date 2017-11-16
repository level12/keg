import logging

import click

from .app import CLI2App

log = logging.getLogger(__name__)


@CLI2App.cli.command('hello1')
def hello1():
    click.echo('hello1')


@CLI2App.cli.command()
def is_quiet():
    print('printed foo')
    log.info('logged foo')


@CLI2App.cli.command()
def is_not_quiet():
    print('printed foo')
    log.info('logged foo')
