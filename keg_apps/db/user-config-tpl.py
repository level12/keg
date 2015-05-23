
class TestProfile(object):
    # These binds are used to test keg dialect functionality. All other database tests
    # are done on the primary connection, which defaults to SQLite.
    SQLALCHEMY_BINDS = {
        # Change the postgres database connection to a database dedicated to Keg tests.
        'postgres': 'postgresql://user:password@localhost/database',
        'sqlite2': 'sqlite:///'
    }
