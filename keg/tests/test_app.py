from __future__ import absolute_import

import pytest

from keg.app import Keg, KegAppError
from keg_apps.cli2.app import CLI2App


class TestInit(object):

    def test_init_called_twice_error(self):
        with pytest.raises(KegAppError, match=r'init\(\) already called on this instance'):
            app = CLI2App(__name__)
            app.init(use_test_profile=True)
            app.init(use_test_profile=True)


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
