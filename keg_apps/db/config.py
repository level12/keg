
class DefaultProfile(object):
    KEG_KEYRING_ENABLE = False

    KEG_REGISTERED_COMPONENTS = {
        'keg_apps.db.blog',
    }


class TestProfile(object):
    KEG_DB_DIALECT_OPTIONS = {
        'postgresql.schemas': ('public', 'fooschema'),
        'mssql.schemas': ('fooschema', ),
    }

    # These binds are used to test keg dialect functionality in CircleCI. All other database tests
    # are done on the primary connection, which defaults to SQLite.
    #
    # Appveyor: see user-config-tpl-appveyor.py
    # Developers: see instructions in readme for setup of local config file
    SQLALCHEMY_BINDS = {
        'postgres': 'postgresql://postgres:password@localhost/postgres',
        'sqlite2': 'sqlite:///'
    }
