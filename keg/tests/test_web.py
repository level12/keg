from keg.testing import WebBase

from keg_apps.web.app import WebApp


class TestBaseView(WebBase):
    appcls = WebApp

    def test_method_routing(self):
        resp = self.testapp.get('/method-routing')
        assert resp.body == 'method get'

        resp = self.testapp.post('/method-routing')
        assert resp.body == 'method post'

    def test_explicit_route(self):
        resp = self.testapp.get('/')
        assert resp.body == 'get explicit'

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
        assert resp.body == 'get explicit'

    def test_templating(self):
        resp = self.testapp.get('/template1')
        assert resp.body == 'Hello world!'

    def test_custom_name(self):
        resp = self.testapp.get('/template2')
        assert resp.body == 'template-too'

    def test_index_route(self):
        resp = self.testapp.get('/routing')
        assert resp.body == 'read'

    def test_post_route(self):
        resp = self.testapp.get('/routing/create')
        assert resp.body == 'create get'

        resp = self.testapp.get('/routing/create')
        assert resp.body == 'create get'

    def test_relative_url(self):
        resp = self.testapp.get('/routing/update/7')
        assert resp.body == 'get update 7'

        resp = self.testapp.post('/routing/update/7')
        assert resp.body == 'post update 7'
