import os

import pytest

from keg.assets import AssetManager, AssetException
from keg_apps.templating.app import TemplatingApp


@pytest.fixture(scope='module')
def app():
    return TemplatingApp.testing_prep()


@pytest.fixture
def am(app):
    return AssetManager(app)


class TestAssets(object):

    def test_load_related(self, am):
        am.load_related('assets_in_template.html')

        assert len(am.content['js']) == 1
        asset_name, filepath, content = am.content['js'].pop()
        assert asset_name == 'assets_in_template.js'
        assert filepath.endswith(
            os.path.join('keg_apps', 'templating', 'templates', 'assets_in_template.js')
        )
        assert content.strip() == '//assets_in_template js file'

        assert len(am.content['css']) == 1
        asset_name, filepath, content = am.content['css'].pop()
        assert asset_name == 'assets_in_template.css'
        assert filepath.endswith(
            os.path.join('keg_apps', 'templating', 'templates', 'assets_in_template.css')
        )
        assert content.strip() == '/* assets_in_template css file */'

    def test_load_related_none_found(self, am):
        with pytest.raises(AssetException) as e:
            am.load_related('_not_there.html')
            assert str(e) == 'Could not find related assets for template: _not_there.html'

    def test_load_single_asset(self, am):
        am.load_related('assets_include_single.html')

        assert len(am.content['js']) == 1
        assert len(am.content['css']) == 0
