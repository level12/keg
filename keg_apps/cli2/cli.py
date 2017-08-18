import logging

import click
import flask

from .app import CLI2App


@CLI2App.cli.command('hello1')
def hello1():
    click.echo('hello1')


@CLI2App.cli.command()
def is_quiet():
    assert flask.current_app.logging.logging_level == logging.WARN


@CLI2App.cli.command()
def is_not_quiet():
    assert flask.current_app.logging.logging_level == logging.INFO
