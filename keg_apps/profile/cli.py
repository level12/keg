from __future__ import absolute_import
from __future__ import print_function

import click
import keg
from keg_apps.profile.app import ProfileApp


def cli_entry():
    ProfileApp.cli.main()


@ProfileApp.cli.command()
def show_profile():
    click.echo(keg.current_app.config['PROFILE_FROM'])


if __name__ == '__main__':
    cli_entry()
