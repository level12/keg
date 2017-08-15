from __future__ import absolute_import

from blazeutils.testing import raises

from keg.app import Keg, KegAppError


class TestInit(object):

    @raises(KegAppError, 'init() already called')
    def test_init_called_twice_error(self):
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
