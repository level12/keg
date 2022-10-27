from unittest import mock

import pytest
import sqlalchemy as sa

from keg.app import Keg, KegAppError
from keg_apps.cli2.app import CLI2App
from keg_apps.db2 import DB2App


class TestInit(object):

    def test_init_called_twice_error(self):
        with pytest.raises(KegAppError, match=r'init\(\) already called on this instance'):
            app = CLI2App(__name__)
            app.init(use_test_profile=True)
            app.init(use_test_profile=True)


class TestSQLitePragma:
    @mock.patch('keg.db.sa_event', autospec=True, spec_set=True)
    def test_config_set(self, m_sa_event):
        DB2App.testing_prep(KEG_SQLITE_ENABLE_FOREIGN_KEYS=True)
        m_sa_event.listens_for.assert_called_once_with(sa.engine.Engine, 'connect')

    @mock.patch('keg.db.sa_event', autospec=True, spec_set=True)
    def test_config_not_set(self, m_sa_event):
        DB2App.testing_prep()
        m_sa_event.listens_for.assert_not_called()


class TestRouteDecorator(object):
    class TRDApp(Keg):
        import_name = __name__ + ':TRDApp'

    class TRDApp2(Keg):
        import_name = __name__ + ':TRDApp2'

    def test_class_method(self):
        @self.TRDApp.route('/foo')
        def foo():
            pass

        @self.TRDApp.route('/bar')
        def bar():
            pass

        @self.TRDApp2.route('/baz')
        def baz():
            pass

        assert len(self.TRDApp._routes) == 2
        assert len(self.TRDApp2._routes) == 1
