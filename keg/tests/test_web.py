from __future__ import absolute_import
from __future__ import unicode_literals

from keg.testing import WebBase

from keg_apps.web.app import WebApp


class TestBaseViewFeatures(WebBase):
    appcls = WebApp

    def test_auto_assign(self):
        resp = self.testapp.get('/auto-assign')
        lines = resp.body.splitlines()
        assert lines[0] == 'bar = bar'
        assert lines[1] == 'baz = baz'
        assert lines[2] == 'foo = none'

    def test_no_auto_assign_with_response(self):
        resp = self.testapp.get('/auto-assign-with-response')
        lines = resp.body.splitlines()
        assert lines[0] == 'bar = '
