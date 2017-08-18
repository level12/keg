from __future__ import absolute_import
from __future__ import print_function

from keg_apps.web.app import WebApp


def cli_entry():
    WebApp.cli.main()


if __name__ == '__main__':
    cli_entry()
