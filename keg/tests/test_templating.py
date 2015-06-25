from __future__ import absolute_import
from __future__ import unicode_literals

from keg import current_app
from keg_apps.templating.app import TemplatingApp


def setup_module(module):
    TemplatingApp.testing_prep()


class TestAssetsInclude(object):
    def render(self, filename):
        template = current_app.jinja_env.get_template(filename)
        return template.render()

    def setup_method(self, method):
        self.ctx = current_app.test_request_context()
        self.ctx.push()
        self.assets = self.ctx.assets

    def teardown_method(self, method):
        self.ctx.pop()

    def test_assets_include(self):
        resp = self.render('assets_in_template.html')
        assert resp.strip() == ''

        assert len(self.assets.content['js']) == 1
        asset_name, filepath, content = self.assets.content['js'].pop()
        assert asset_name == 'assets_in_template.js'
        assert filepath.endswith('keg_apps/templating/templates/assets_in_template.js')
        assert content.strip() == '//assets_in_template js file'

        assert len(self.assets.content['css']) == 1
        asset_name, filepath, content = self.assets.content['css'].pop()
        assert asset_name == 'assets_in_template.css'
        assert filepath.endswith('keg_apps/templating/templates/assets_in_template.css')
        assert content.strip() == '/* assets_in_template css file */'
