from __future__ import absolute_import
from __future__ import unicode_literals

import mock

from keg.app import Keg
from keg.config import Config


class TestConfigDefaults(object):

    def test_default_profile(self):
        app = Keg(__name__).init()
        assert app.config_profile is None
        assert app.config.profile is None

        # this key comes from Keg's DefaultProfile
        assert 'KEG_ENDPOINTS' in app.config

    def test_app_params_profile(self):
        app = Keg(__name__, config_profile='Foo').init()
        assert app.config_profile == 'Foo'
        assert app.config.profile == 'Foo'

    @mock.patch.dict('os.environ', {'TEMPAPP_CONFIG_PROFILE': 'bar'})
    def test_environ_profile(self):
        app = Keg('tempapp').init()
        assert app.config_profile is None
        assert app.config.profile == 'bar'

    def test_profile_from_config_file(self):
        config_file_objs = [('/fake/path', dict(DEFAULT_PROFILE='baz'))]
        config = Config('', {})
        config.init_app(None, __name__, '', config_file_objs)
        assert config.profile == 'baz'

    def test_default_config_objects_no_profile(self):
        config = Config('', {})
        config.init_app(None, 'fakeapp', '')

        # No profile given, so only the default profiles from Keg and the App should be tried.
        expected = [
            'keg.config.DefaultProfile',
            'fakeapp.config.DefaultProfile'
        ]
        assert config.default_config_locations_parsed() == expected

    def test_default_config_objects_with_profile(self):
        config = Config('', {})

        config.init_app('SomeProfile', 'fakeapp', '')

        # No profile given, so only the default profiles from Keg and the App should be tried.
        expected = [
            'keg.config.DefaultProfile',
            'keg.config.SomeProfile',
            'fakeapp.config.DefaultProfile',
            'fakeapp.config.SomeProfile',
        ]
        assert config.default_config_locations_parsed() == expected

    def test_config_substitutions(self):
        config = Config('', {})
        config['testvalue'] = '{not there}'
        config.init_app(None, 'fakeapp', '')
        assert config['KEG_LOG_DPATH'] == config.dirs.user_log_dir
        assert config['KEG_LOG_FNAME'] == 'fakeapp.log'
        assert config['testvalue'] == '{not there}'
