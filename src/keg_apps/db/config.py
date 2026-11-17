from importlib.util import find_spec


class DefaultProfile:
    KEG_KEYRING_ENABLE = False

    KEG_REGISTERED_COMPONENTS = {
        'keg_apps.db.blog',
    }


class TestProfile:
    KEG_DB_DIALECT_OPTIONS = {
        'postgresql.schemas': ('public', 'barschema'),
        'bind.postgres.schemas': ('public', 'fooschema'),
        'mssql.schemas': ('fooschema',),
    }

    # These binds are used to test Keg dialect functionality in CI. All other database tests
    # are done on the primary connection, which defaults to SQLite.
    #
    # Developers: see instructions in the readme for setup of a local config file.
    SQLALCHEMY_BINDS = {
        # This string will connect to the postgresql DB setup in docker-compose.yaml and
        # work in CircleCI.
        'postgres': 'postgresql://postgres@127.0.0.1:54321/postgres',
        'sqlite2': 'sqlite:///',
    }
    # The legacy MSSQL dialect has no wheels for current Python versions, so exercise it only when
    # a developer has explicitly installed the optional test dependencies.
    if find_spec('sqlalchemy_pyodbc_mssql'):
        SQLALCHEMY_BINDS['mssql'] = (
            'mssql+pyodbc_mssql://sa:Password12!@127.0.0.1:14331/tempdb'
            '?driver=ODBC+Driver+17+for+SQL+Server'
        )
