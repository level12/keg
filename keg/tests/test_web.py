import flask
from keg.component import KegComponent
from keg.testing import WebBase

from keg_apps.web.app import WebApp


class TestBaseViewFeatures(WebBase):
    appcls = WebApp

    def test_auto_assign(self):
        resp = self.testapp.get('/auto-assign')
        lines = resp.body.splitlines()
        assert lines[0] == b'bar = bar'
        assert lines[1] == b'baz = baz'
        assert lines[2] == b'foo = none'

    def test_no_auto_assign_with_response(self):
        resp = self.testapp.get('/auto-assign-with-response')
        lines = resp.body.splitlines()
        assert lines[0] == b'bar = '

    def test_empty_string_response(self):
        resp = self.testapp.get('/blank-view')
        assert resp.body == b''

    def test_pre_response_middleware(self):
        # Test that response is available to pre_response
        resp = self.testapp.get('/response-middleware/foo')
        assert resp.body == b'foo_test'

        # Test that original response returned when pre_response does not
        # return
        resp = self.testapp.get('/response-middleware/bar')
        assert resp.body == b'bar'

        # Test empty response allowed from pre_response
        resp = self.testapp.get('/response-middleware/baz')
        assert resp.body == b''


class TestBlueprintUsage(WebBase):
    appcls = WebApp

    def test_blueprint_url_prefix(self):
        self.testapp.get('/tanagra/blueprint-test')

    def test_blueprint_template_folder(self):
        resp = self.testapp.get('/tanagra/blueprint-test')
        assert 'blueprint template found ok' in resp


class TestComponentBlueprint(WebBase):
    appcls = WebApp

    def test_component_blueprint_loads(self):
        resp = self.testapp.get('/blog')
        assert 'I am a blog' in resp

    def test_component_blueprint_base(self):
        class CustomBlueprint(flask.Blueprint):
            pass

        component = KegComponent('foo')
        bp = component.create_blueprint('test_blueprint', __name__, blueprint_cls=CustomBlueprint)
        assert isinstance(bp, CustomBlueprint)
