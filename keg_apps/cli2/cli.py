import click

from .app import CLI2App


@CLI2App.cli.command('hello1')
def hello1():
    click.echo('hello1')
