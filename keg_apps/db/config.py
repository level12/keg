
class DefaultProfile(object):
    KEG_KEYRING_ENABLE = False

    KEG_REGISTERED_COMPONENTS = {
        'keg_apps.db.blog',
    }


class TestProfile(object):
    KEG_DB_DIALECT_OPTIONS = {
        'postgresql.schemas': ('public', 'barschema'),
        'bind.postgres.schemas': ('public', 'fooschema'),
        'mssql.schemas': ('fooschema', ),
    }

    # These binds are used to test keg dialect functionality in CircleCI. All other database tests
    # are done on the primary connection, which defaults to SQLite.
    #
    # Appveyor: see user-config-tpl-appveyor.py
    # Developers: see instructions in readme for setup of local config file
    SQLALCHEMY_BINDS = {
        # This string will connect to the postgresql DB setup in docker-compose.yaml and
        # work in CircleCI.
        'postgres': 'postgresql://postgres@127.0.0.1:54321/postgres',
        'mssql': 'mssql+pyodbc_mssql://sa:Password12!@127.0.0.1:14331/tempdb'
        '?driver=ODBC+Driver+17+for+SQL+Server',
        'sqlite2': 'sqlite:///'
    }
