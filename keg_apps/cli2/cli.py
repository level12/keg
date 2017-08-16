import click

from .app import CLI2App


@CLI2App.command('hello1')
def hello1():
    click.echo('hello1')
