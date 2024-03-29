from unittest import mock

import pytest
import sqlalchemy as sa

from keg import current_app
from keg.db import db

from keg_apps.db.app import DBApp


@pytest.fixture(scope="module", autouse=True)
def app():
    app = DBApp.testing_prep()
    # Setup an app context that clears itself when this module's tests are finished.
    with app.app_context():
        yield


@pytest.fixture(autouse=True)
def db_session_prep():
    """
        Rollback the session after every test.
    """
    db.session.rollback()


class DialectExam(object):
    bind_name = None
    obj_names_sql = None

    @classmethod
    def dialect(cls):
        return current_app.db_manager.bind_dialect(cls.bind_name)

    def engine(self):
        return db.get_engine(current_app, self.bind_name)

    def obj_names(self):
        with self.engine().begin() as conn:
            records = conn.execute(sa.text(self.obj_names_sql)).fetchall()
        return set([record[0] for record in records])

    def create_objs(self):
        with self.engine().begin() as conn:
            conn.execute(sa.text('create table foo(label varchar(20))'))
            conn.execute(sa.text('create view vfoo as select * from foo'))
        return 2

    def test_database_clearing(self):
        obj_count = self.create_objs()
        # Expected count after creation is the number of objects created specifically for this test
        # plus the number of tables created for each entity defined in this test app.
        assert len(self.obj_names()) == obj_count + self.entity_count
        self.dialect().drop_all()
        assert len(self.obj_names()) == 0

    def test_create_all(self):
        self.dialect().drop_all()
        self.dialect().create_all()
        assert len(self.obj_names()) == self.entity_count


class TestSQLite(DialectExam):
    bind_name = 'sqlite2'
    obj_names_sql = "select name from sqlite_master where type in ('table', 'view')"
    # How many entities exist for this bind in the application?
    entity_count = 1


class TestPostgreSQL(DialectExam):
    bind_name = 'postgres'
    obj_names_sql = ("SELECT table_schema || '.' || table_name FROM INFORMATION_SCHEMA.tables"
                     " WHERE table_type in ('BASE TABLE', 'VIEW')"
                     " AND table_schema in ('public', 'fooschema')")
    # How many entities exist for this bind in the application?
    entity_count = 2

    def create_objs(self):
        with self.engine().begin() as conn:
            conn.execute(sa.text('create table foo(label varchar(20))'))
            conn.execute(sa.text('create view vfoo as select * from foo'))
            conn.execute(sa.text('create table fooschema.bar(label varchar(20))'))
            conn.execute(sa.text('create view fooschema.vbar as select * from fooschema.bar'))
        return 4

    def test_create_all_without_prepping(self):
        """Test that create_all creates necessary schemas"""
        self.dialect().drop_all()
        self.dialect().create_all()
        assert len(self.obj_names()) == self.entity_count

    def test_create_all_existing_schemas(self):
        """Test that create_all can be called when schemas already exist"""
        self.dialect().drop_all()
        self.dialect().create_all()
        self.dialect().create_all()
        assert len(self.obj_names()) == self.entity_count

    def test_options_follow_bind_dialect_specificity(self):
        """Test that create_all creates necessary schemas from the dialect option"""
        dialect_config = current_app.config.get('KEG_DB_DIALECT_OPTIONS').copy()
        del dialect_config['bind.postgres.schemas']
        with mock.patch.object(current_app.db_manager, 'dialect_opts', dialect_config):
            dialect = self.dialect()
            assert dialect.opt_schemas == ('public', 'barschema')
        dialect = self.dialect()
        assert dialect.opt_schemas == ('public', 'fooschema')


class TestMicrosoftSQL(DialectExam):
    bind_name = 'mssql'
    # MSSQL supports the INFORMATION_SCHEMA standard
    obj_names_sql = (
        "SELECT table_schema + '.' + table_name FROM INFORMATION_SCHEMA.tables"
        " WHERE table_type in ('BASE TABLE', 'VIEW')"
        " AND table_schema in ('dbo', 'fooschema')"
        " AND table_name not like '#%'"  # Avoid cached temporary tables
    )
    # How many entities exist for this bind in the application?
    entity_count = 2

    def setup_method(self, method):
        if 'mssql' not in current_app.config.get('SQLALCHEMY_BINDS', {}):
            pytest.skip('cannot test missing bind for mssql')

    def create_objs(self):
        with self.engine().begin() as conn:
            conn.execute(sa.text('create table foo(label varchar(20))'))
            conn.execute(sa.text('create view vfoo as select * from foo'))
            conn.execute(sa.text('create table fooschema.bar(label varchar(20))'))
            conn.execute(sa.text('create view fooschema.vbar as select * from fooschema.bar'))
        return 4

    def test_create_all_without_prepping(self):
        """Test that create_all creates necessary schemas"""
        self.dialect().drop_all()
        self.dialect().create_all()
        assert len(self.obj_names()) == self.entity_count

    def test_create_all_existing_schemas(self):
        """Test that create_all can be called when schemas already exist"""
        self.dialect().drop_all()
        self.dialect().create_all()
        self.dialect().create_all()
        assert len(self.obj_names()) == self.entity_count
