from __future__ import absolute_import
from __future__ import unicode_literals
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
