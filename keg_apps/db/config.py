
class DefaultProfile(object):
    KEG_KEYRING_ENABLE = False


class TestProfile(object):
    KEG_DB_DIALECT_OPTIONS = {
        'postgresql.schemas': ('public', 'fooschema'),
        'mssql.schemas': ('fooschema', ),
    }

    # These binds are used to test keg dialect functionality in CircleCI. All other database tests
    # are done on the primary connection, which defaults to SQLite.
    #
    # Appveyor: see user-config-tpl-appveyor.py
    #
    # Developers: setup a TestProfile config for these tests in file:
    # <keg src>/keg_apps.db-config.py
    SQLALCHEMY_BINDS = {
        'postgres': 'postgresql://postgres:password@localhost/postgres',
        'sqlite2': 'sqlite:///'
    }
