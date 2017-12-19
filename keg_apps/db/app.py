from __future__ import absolute_import

from keg.app import Keg


class DBApp(Keg):
    import_name = 'keg_apps.db'
    db_enabled = True


@DBApp.cli.command()
def hello():
    print('hello db cli')


if __name__ == '__main__':
    DBApp.cli.main()
