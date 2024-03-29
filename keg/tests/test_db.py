import pytest

from keg import current_app
from keg.db import db
from keg.signals import db_init_pre, db_init_post, db_clear_post, db_clear_pre
from keg.testing import invoke_command

# Note: we do not want to import Blog directly here. Doing so will affect metadata collection and
# prevent the tests below from proving that component initialization is loading the model.
# from keg_apps.db.blog.model.entities import Blog
import keg_apps.db.model.entities as ents
from keg_apps.db.app import DBApp
from keg_apps.db2 import DB2App


class TestDB(object):

    @pytest.fixture(scope="class", autouse=True)
    def setup_app(self):
        app = DBApp.testing_prep()
        # Setup an app context that clears itself when this class's tests are finished.
        with app.app_context():
            yield

    def teardown_method(self):
        db.session.rollback()

    def test_primary_db_entity(self):
        # importing Blog here to ensure we're importing after app init, which will only succeed if
        # the component has loaded properly
        from keg_apps.db.blog.model.entities import Blog
        assert Blog.query.count() == 0
        blog = Blog(title='foo')
        db.session.add(blog)
        db.session.commit()
        assert Blog.query.count() == 1

    def test_postgres_bind_db_entity(self):
        assert ents.PGDud.query.count() == 0
        dud = ents.PGDud(name='foo')
        db.session.add(dud)
        db.session.commit()
        assert ents.PGDud.query.count() == 1

    def test_postgres_db_enttity_alt_schema(self):
        assert ents.PGDud2.query.count() == 0
        dud = ents.PGDud2(name='foo')
        db.session.add(dud)
        db.session.commit()
        assert ents.PGDud2.query.count() == 1


class TestDB2(object):

    def test_init_without_db_binds(self):
        # Make sure we don't get an error initializing the app when the SQLALCHEMY_BINDS config
        # option is None
        app = DB2App.testing_prep()
        value = app.config.get('SQLALCHEMY_BINDS')
        # flask-sqlalchemy < 3.0: None
        # flask-sqlalchemy 3.0+: {}
        assert value is None or value == {}


class TestDatabaseManager(object):

    @pytest.fixture(scope="class", autouse=True)
    def setup_app(self):
        app = DBApp.testing_prep()
        # Setup an app context that clears itself when this class's tests are finished.
        with app.app_context():
            yield

    def teardown_method(self):
        db.session.rollback()

    def test_db_init_with_clear(self):
        # importing Blog here to ensure we're importing after app init, which will only succeed if
        # the component has loaded properly
        from keg_apps.db.blog.model.entities import Blog

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

        Blog.testing_create()
        assert Blog.query.count() >= 1
        ents.PGDud2.testing_create()
        assert ents.PGDud2.query.count() >= 1

        current_app.db_manager.db_init_with_clear()

        # todo: We could check all the intermediate steps, but this is more a functional test
        # for now.  If the record is gone and we can create an new blog post, then we assume the
        # clear and init went ok.
        assert Blog.query.count() == 0
        Blog.testing_create()
        assert Blog.query.count() == 1

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
