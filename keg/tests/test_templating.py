import os

from jinja2 import TemplateSyntaxError
import pytest

from keg_apps.templating.app import TemplatingApp


@pytest.fixture(scope="module")
def app():
    return TemplatingApp.testing_prep()


class TestAssetsInclude(object):

    @pytest.fixture(autouse=True)
    def setup_teardown(self, app):
        # setup
        self.ctx = app.test_request_context()
        self.ctx.push()
        self.assets = self.ctx.assets
        self.app = app
        yield
        # teardown
        self.ctx.pop()

    def render(self, filename):
        template = self.app.jinja_env.get_template(filename)
        return template.render()

    def test_include(self, app):
        resp = self.render('assets_in_template.html')
        assert resp.strip() == ''

        assert len(self.assets.content['js']) == 1
        asset_name, filepath, content = self.assets.content['js'].pop()
        assert asset_name == 'assets_in_template.js'
        assert filepath.endswith(
            os.path.join('keg_apps', 'templating', 'templates', 'assets_in_template.js')
        )
        assert content.strip() == '//assets_in_template js file'

        assert len(self.assets.content['css']) == 1
        asset_name, filepath, content = self.assets.content['css'].pop()
        assert asset_name == 'assets_in_template.css'
        assert filepath.endswith(
            os.path.join('keg_apps', 'templating', 'templates', 'assets_in_template.css')
        )
        assert content.strip() == '/* assets_in_template css file */'

    def test_include_with_params(self):
        with pytest.raises(TemplateSyntaxError) as e:
            self.render('assets_with_params.html')
            assert str(e) == 'asset_include does not yet support parameters'

    def test_assets_content(self):
        self.ctx.assets.content['css'].append(('fake-file.css', 'foo', '//fake-file.css content'))
        self.ctx.assets.content['js'].append(('fake-file.js', 'foo', '//fake-file.js content'))
        resp = self.render('assets_content.html')
        lines = resp.splitlines()
        assert lines[0] == '/********************* asset: fake-file.css *********************/'
        # skip newline that combine_content() adds
        assert lines[2] == '//fake-file.css content'
        assert lines[3] == '/********************* asset: fake-file.js *********************/'
        # skip newline that combine_content() adds
        assert lines[5] == '//fake-file.js content'
