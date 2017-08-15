from __future__ import absolute_import

import flask
import flask_webtest
from keg_apps.flaskwtf_bug import BugFixApp, BugApp


class TestViewRouting(object):

    def test_bug_presence(self):
        """ This test will BREAK when the bug is no longer present upstream, at which point this
        fix can be considered for removal.  """
        app = BugApp.testing_prep(FIX_FLASK_WTF_BUG=False)
        client = flask_webtest.TestApp(app)
        client.get('/form')
        assert 'csrf_token' in flask.g

    def test_bug_fix(self):
        app = BugFixApp.testing_prep()
        client = flask_webtest.TestApp(app)
        client.get('/form')
        assert 'csrf_token' not in flask.g
