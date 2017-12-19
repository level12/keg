from __future__ import absolute_import

import pytest

from keg import current_app
from keg.db import db
from keg.signals import db_init_pre, db_init_post, db_clear_post, db_clear_pre
from keg.testing import invoke_command

import keg_apps.db.model.entities as ents
from keg_apps.db.app import DBApp
from keg_apps.db2 import DB2App


@pytest.fixture(autouse=True)
def db_session_prep():
    """
        Rollback the session after every test.
    """
    db.session.rollback()


class TestDB(object):

    @classmethod
    def setup_class(cls):
        DBApp.testing_prep()

    def test_primary_db_entity(self):
        assert ents.Blog.query.count() == 0
        blog = ents.Blog(title=u'foo')
        db.session.add(blog)
        db.session.commit()
        assert ents.Blog.query.count() == 1

    def test_postgres_bind_db_entity(self):
        assert ents.PGDud.query.count() == 0
        dud = ents.PGDud(name=u'foo')
        db.session.add(dud)
        db.session.commit()
        assert ents.PGDud.query.count() == 1

    def test_postgres_db_enttity_alt_schema(self):
        assert ents.PGDud2.query.count() == 0
        dud = ents.PGDud2(name=u'foo')
        db.session.add(dud)
        db.session.commit()
        assert ents.PGDud2.query.count() == 1


class TestDB2(object):

    def test_init_without_db_binds(self):
        # Make sure we don't get an error initializing the app when the SQLALCHEMY_BINDS config
        # option is None
        app = DB2App.testing_prep()
        assert app.config.get('SQLALCHEMY_BINDS') is None


class TestDatabaseManager(object):
    @classmethod
    def setup_class(cls):
        DBApp.testing_prep()

    def test_db_init_with_clear(self):
        # have to use self here to enable the inner functions to adjust an outer-context variable
        self.init_pre_connected = False
        self.init_post_connected = False
        self.clear_pre_connected = False
        self.clear_post_connected = False

        @db_init_pre.connect_via(current_app._get_current_object())
        def catch_init_pre(app):
            self.init_pre_connected = True

        @db_init_post.connect_via(current_app._get_current_object())
        def catch_init_post(app):
            self.init_post_connected = True

        @db_clear_pre.connect_via(current_app._get_current_object())
        def catch_clear_pre(app):
            self.clear_pre_connected = True

        @db_clear_post.connect_via(current_app._get_current_object())
        def catch_clear_post(app):
            self.clear_post_connected = True

        ents.Blog.testing_create()
        assert ents.Blog.query.count() >= 1
        ents.PGDud2.testing_create()
        assert ents.PGDud2.query.count() >= 1

        current_app.db_manager.db_init_with_clear()

        # todo: We could check all the intermediate steps, but this is more a functional test
        # for now.  If the record is gone and we can create an new blog post, then we assume the
        # clear and init went ok.
        assert ents.Blog.query.count() == 0
        ents.Blog.testing_create()
        assert ents.Blog.query.count() == 1

        assert self.init_pre_connected
        assert self.init_post_connected
        assert self.clear_pre_connected
        assert self.clear_post_connected


class TestKegSQLAlchemy(object):
    def test_session_ids_with_cli_invocation(self):
        sess_id = id(db.session)

        result = invoke_command(DBApp, 'hello')
        assert 'hello db cli' in result.output

        assert id(db.session) == sess_id
