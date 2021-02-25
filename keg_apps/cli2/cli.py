import logging

import click

from .app import CLI2App

log = logging.getLogger(__name__)


@CLI2App.cli.command('hello1')
def hello1():
    click.echo('hello1')


@CLI2App.cli.command('test-log-level')
def test_log_level():
    print('printed foo')
    log.debug('debug logged foo')
    log.info('info logged foo')
    log.warning('warning logged foo')
    log.error('error logged foo')
    log.critical('critical logged foo')


@CLI2App.cli.command()
def reverse():
    data = click.prompt('Input')
    click.echo(data[::-1])
