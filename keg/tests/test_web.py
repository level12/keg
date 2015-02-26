from keg_apps.web.app import WebApp
from keg.testing import WebBase


class TestPublicView(WebBase):
    appcls = WebApp

    def test_implicit_route(self):
        resp = self.testapp.get('/some-view')
        assert resp.body == 'hi from SomeView'

    def test_explicit_route(self):
        resp = self.testapp.get('/')
        assert resp.body == 'home'

    def test_urls_routes(self):
        resp = self.testapp.get('/hello')
        assert resp.body == 'Hello World'

        resp = self.testapp.get('/hello/sam')
        assert resp.body == 'Hello sam'

    def test_multiple_applications(self):
        # there is already an application created due to WebBase.setup_class()...create another
        # one explicitly.
        WebApp(config_profile='TestingProfile').init()
        resp = self.testapp.get('/')
        assert resp.body == 'home'

    def test_templating(self):
        resp = self.testapp.get('/template1')
        assert resp.body == 'Hello world!'

    def test_custom_name(self):
        resp = self.testapp.get('/template2')
        assert resp.body == 'template-too'
