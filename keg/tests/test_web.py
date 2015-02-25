from keg_apps.web import WebApp
from keg.testing import WebBase


class TestPublicView(WebBase):
    appcls = WebApp

    def test_automatic_route(self):
        resp = self.testapp.get('/some-view')
        assert resp.body == 'hi from SomeView'

    def test_urls_routes(self):
        resp = self.testapp.get('/hello')
        assert resp.body == 'Hello World'

        resp = self.testapp.get('/hello/sam')
        assert resp.body == 'Hello sam'
