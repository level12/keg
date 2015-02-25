import sqlite3

from blinker import ANY
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event

from keg.signals import testing_run_start


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

        @testing_run_start.connect_via(ANY, weak=False)
        def on_testing_start(app):
            self.on_testing_start(app)

    def testing_scoped_session(self):
        # don't want to have to import this if we are in production, so put import
        # inside of the method
        from flask.ext.webtest import get_scopefunc

        # flask-sqlalchemy creates the session when the class is initialized.  We have to re-create
        # with different session options and override the session attribute with the new session
        db.session = db.create_scoped_session(options={'scopefunc': get_scopefunc()})

    def clear_db(self):
        if db.engine.dialect.name == 'postgresql':
            sql = []
            sql.append('DROP SCHEMA public cascade;')
            sql.append('CREATE SCHEMA public AUTHORIZATION {0};'.format(db.engine.url.username))
            sql.append('GRANT ALL ON SCHEMA public TO {0};'.format(db.engine.url.username))
            sql.append('GRANT ALL ON SCHEMA public TO public;')
            sql.append("COMMENT ON SCHEMA public IS 'standard public schema';")
            for exstr in sql:
                try:
                    db.engine.execute(exstr)
                except Exception, e:
                    print 'WARNING: {0}'.format(e)
        elif db.engine.dialect.name == 'sqlite':
            # drop the views
            sql = "select name from sqlite_master where type='view'"
            rows = db.engine.execute(sql)
            # need to get all views before start to try and delete them, otherwise
            # we will get "database locked" errors from sqlite
            records = rows.fetchall()
            for row in records:
                db.engine.execute('drop view {0}'.format(row['name']))

            # drop the tables
            db.metadata.reflect(bind=db.engine)
            for table in reversed(db.metadata.sorted_tables):
                try:
                    table.drop(db.engine)
                except Exception, e:
                    if not 'no such table' in str(e):
                        raise
        elif db.engine.dialect.name == 'mssql':
            mapping = {
                'P': 'drop procedure [{name}]',
                'C': 'alter table [{parent_name}] drop constraint [{name}]',
                ('FN', 'IF', 'TF'): 'drop function [{name}]',
                'V': 'drop view [{name}]',
                'F': 'alter table [{parent_name}] drop constraint [{name}]',
                'U': 'drop table [{name}]',
            }
            delete_sql = []
            for type, drop_sql in mapping.iteritems():
                sql = 'select name, object_name( parent_object_id ) as parent_name '\
                    'from sys.objects where type in (\'{0}\')'.format("', '".join(type))
                rows = db.engine.execute(sql)
                for row in rows:
                    delete_sql.append(drop_sql.format(**dict(row)))
            for sql in delete_sql:
                db.engine.execute(sql)
        else:
            return False
        return True

    def on_testing_start(self, app):
        print 'on testing start'
        self.clear_db()
        db.create_all()


db = KegSQLAlchemy()
