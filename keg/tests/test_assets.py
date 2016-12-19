from __future__ import absolute_import

import os

import pytest
import six

import keg
from keg.assets import AssetManager, AssetException
from keg_apps.templating.app import TemplatingApp


def setup_module(module):
    TemplatingApp.testing_prep()


class TestAssets(object):

    def test_load_related(self):
        am = AssetManager(keg.current_app)
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

    def test_load_related_none_found(self):
        with pytest.raises(AssetException) as e:
            am = AssetManager(keg.current_app)
            am.load_related('_not_there.html')
            assert six.text_type(e) == 'Could not find related assets for template: _not_there.html'

    def test_load_single_asset(self):
        am = AssetManager(keg.current_app)
        am.load_related('assets_include_single.html')

        assert len(am.content['js']) == 1
        assert len(am.content['css']) == 0
