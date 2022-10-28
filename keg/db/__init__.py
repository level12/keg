import flask_sqlalchemy as fsa
import sqlalchemy as sa
import sqlalchemy.event as sa_event

from keg.signals import (
    db_before_import,
    db_clear_post,
    db_clear_pre,
    db_init_post,
    db_init_pre,
    testing_run_start,
)
from keg.utils import visit_modules


class KegSQLAlchemy(fsa.SQLAlchemy):
    def _apply_driver_defaults(self, options, app):
        """Override some driver specific settings"""
        super_return_value = None
        if hasattr(super(), '_apply_driver_defaults'):
            super_return_value = super()._apply_driver_defaults(options, app)

        # Turn on SA pessimistic disconnect handling by default:
        # http://docs.sqlalchemy.org/en/latest/core/pooling.html#disconnect-handling-pessimistic
        options.setdefault('pool_pre_ping', True)

        # While this isn't an engine options change, it is in the domain of db engine
        # setup and so belongs here.
        if app.config.get('KEG_SQLITE_ENABLE_FOREIGN_KEYS'):
            sa_event.listens_for(sa.engine.Engine, 'connect')(self._set_sqlite_pragma)

        return super_return_value

    def apply_driver_hacks(self, app, info, options):
        """This method is renamed to _apply_driver_defaults in flask-sqlalchemy 3.0"""
        super_return_value = super().apply_driver_hacks(app, info, options)

        # follow the logic to set some defaults, but the super won't exist there
        self._apply_driver_defaults(options, app)

        return super_return_value

    def get_engine(self, app=None, bind=None):
        if not hasattr(self, '_app_engines'):
            # older version of flask-sqlalchemy, we can just call super
            return super().get_engine(app=app, bind=bind)

        # More recent flask-sqlalchemy, use the cached engines directly.
        # Note: we don't necessarily have an app context active here, depending
        # on if this is being called during app init. But if we attempt to access
        # the underlying cache directly, we get a weak ref error.
        with app.app_context():
            return self.engines[bind]

    def get_engines(self, app):
        # the default engine doesn't have a bind
        retval = [(None, self.get_engine(app))]

        bind_names = app.config['SQLALCHEMY_BINDS']
        # The default value of SQLALCHEMY_BINDS is None and the key is present b/c of
        # Flask-SQLAlchemy defaults.  So, only process the binds if they are not None.
        if bind_names is not None:
            for bind_name in bind_names:
                retval.append((bind_name, self.get_engine(app, bind=bind_name)))

        return retval

    def _set_sqlite_pragma(self, connection, conn_record):
        # Sets a pragma to tell sqlite to not ignore FK constraints.
        from sqlite3 import Connection as SQLite3Connection
        if isinstance(connection, SQLite3Connection):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()


db = KegSQLAlchemy()

# put this import after the above db assignment to avoid circular reference issues
from .dialect_ops import DialectOperations  # noqa


class DatabaseManager(object):
    """
        A per-app-instance utility class that managers all common operations for a Keg app.

        Binds & Dialects
        ----------------

        Flask SQLAlchemy handles multiple DB connections per application through the use of "binds."
        When an application wants to communicate events or initiate activites, this manager will
        will handle distributing those events and activities to all database connections bound
        to the application.

        Furthermore, this manager delegates to DialectOperations instances to run the events and
        activities in ways that are specific to the type of RDBMS being used (when needed).
    """

    def __init__(self, app):
        self.app = app
        self.dialect_opts = app.config['KEG_DB_DIALECT_OPTIONS']

        self.init_app()
        self.init_events()

    def init_app(self):
        db.init_app(self.app)
        db_before_import.send(self.app)
        visit_modules(self.app.db_visit_modules, self.app.import_name)

    def init_events(self):
        testing_run_start.connect(self.on_testing_start, sender=self.app)

    def bind_dialect(self, bind_name):
        engine = db.get_engine(self.app, bind=bind_name)
        return DialectOperations.create_for(engine, bind_name, self.dialect_opts)

    def all_bind_dialects(self):
        """
            For each database connection (bind) in this application, yield a DialectOperations
            instance corresponding to the type of RDBMS the bind is connecting to.
        """
        for bind_name, engine in db.get_engines(self.app):
            yield DialectOperations.create_for(engine, bind_name, self.dialect_opts)

    def on_testing_start(self, app):
        self.db_init_with_clear()

    def create_all(self):
        for dialect in self.all_bind_dialects():
            dialect.create_all()

    def drop_all(self):
        db.session.remove()
        for dialect in self.all_bind_dialects():
            dialect.drop_all()

    # The methods that follow will trigger application events.
    def db_init_with_clear(self):
        self.db_clear()
        self.db_init()

    def db_init(self):
        db_init_pre.send(self.app)
        self.create_all()
        db_init_post.send(self.app)

    def db_clear(self):
        db_clear_pre.send(self.app)
        self.drop_all()
        db_clear_post.send(self.app)
