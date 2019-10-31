
class TestProfile(object):
    # These binds are used to test keg dialect functionality. All other database tests
    # are done on the primary connection, which defaults to SQLite.
    SQLALCHEMY_BINDS = {
        # Change the postgres database connection to a database dedicated to Keg tests.
        'postgres': 'postgresql://postgres:Password12!@localhost/keg_test',
        'mssql': 'mssql+pyodbc_mssql://sa:Password12!@localhost:1433/tempdb'
        '?driver=SQL+Server+Native+Client+11.0',
        'sqlite2': 'sqlite:///'
    }
