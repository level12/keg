from __future__ import absolute_import

import pytest

from keg.app import Keg, KegAppError


class TestInit(object):

    @pytest.mark.skip("Fails when flask version is >1.0")
    def test_init_called_twice_error(self):
        with pytest.raises(KegAppError, match=r'init\(\) already called on this instance'):
            app = Keg(__name__)
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
