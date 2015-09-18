from __future__ import absolute_import
from keg.testing import WebBase

from keg_apps.web.app import WebApp


class TestViewTemplating(WebBase):
    appcls = WebApp

    def test_templating(self):
        resp = self.testapp.get('/template1')
        assert resp.text == 'Hello world!'

    def test_custom_name(self):
        resp = self.testapp.get('/template2')
        assert resp.text == 'template-too'


class TestJinjaInit(WebBase):
    appcls = WebApp

    def test_jinja_filter(self):
        resp = self.testapp.get('/jinja')
        assert resp.text == 'hello Keg foo'
