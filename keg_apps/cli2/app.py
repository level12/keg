from __future__ import absolute_import

from keg.app import Keg


class CLI2App(Keg):
    import_name = 'keg_apps.cli2'

    def on_init_complete(self):
        # Want to test when the CLI command is registered after the app is initialized
        import keg_apps.cli2.cli  # noqa


if __name__ == '__main__':
    # This import prevents a nasty bug where there are actually two classes __main__.CLI2App
    # and the one with a full module path.
    import keg_apps.cli2.app as app
    app.CLI2App.cli.main()
