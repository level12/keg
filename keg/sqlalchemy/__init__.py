import sqlite3

from blinker import ANY
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event

from keg.signals import testing_start


class KegSQLAlchemy(SQLAlchemy):

    def set_sqlite_pragma(self, dbapi_connection, connection_record):
        """ Need SQLite to use foreign keys """
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    def init_app(self, app):
        SQLAlchemy.init_app(self, app)
        if app.testing:
            self.testing_scoped_session()

        @event.listens_for(Engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            self.set_sqlite_pragma(dbapi_connection, connection_record)

        @testing_start.connect_via(ANY, weak=False)
        def on_testing_start(app):
            self.on_testing_start(app)

    def testing_scoped_session(self):
        # don't want to have to import this if we are in production, so put import
        # inside of the method
        from flask.ext.webtest import get_scopefunc

        # flask-sqlalchemy creates the session when the class is initialized.  We have to re-create
        # with different session options and override the session attribute with the new session
        db.session = db.create_scoped_session(options={'scopefunc': get_scopefunc()})

    def on_testing_start(self, app):
        db.create_all()


db = KegSQLAlchemy()

