
class DefaultProfile(object):
    KEG_KEYRING_ENABLE = False


class TestProfile(object):
    KEG_DB_DIALECT_OPTIONS = {
        'postgresql.schemas': ('public', 'fooschema'),
    }

    # These binds are used to test keg dialect functionality. All other database tests
    # are done on the primary connection, which defaults to SQLite.
    SQLALCHEMY_BINDS = {
        # The postgres connection defaults to what our travis build needs.  If testing as a
        # developer, then you should setup a TestProfile config for these tests in
        # file: ~/.config/keg_apps.db/keg_apps.db-config.py
        'postgres': 'postgresql://ubuntu:@localhost/circle_test',
        'sqlite2': 'sqlite:///'
    }
