from __future__ import absolute_import
from __future__ import unicode_literals

import os

import mock

from keg.app import Keg
from keg.config import Config
from keg.testing import invoke_command
from keg_apps.profile.cli import ProfileApp


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


class TestProfileLoading(object):

    def test_app_init(self):
        # the direct setting should override the environment
        kwargs = {'KEG_APPS.PROFILE_CONFIG_PROFILE': 'EnvironmentProfile'}
        with mock.patch.dict(os.environ, **kwargs):
            app = ProfileApp(config_profile='AppInitProfile').init()
        assert app.config['PROFILE_FROM'] == 'app-init'

    def test_config_file_default(self):
        app = ProfileApp().init()
        assert app.config['PROFILE_FROM'] == 'config-file-default'

    def test_testing_default(self):
        app = ProfileApp.testing_prep()
        assert app.config['PROFILE_FROM'] == 'testing-default'

    def test_environment(self):
        kwargs = {'KEG_APPS.PROFILE_CONFIG_PROFILE': 'EnvironmentProfile'}
        with mock.patch.dict(os.environ, **kwargs):
            app = ProfileApp().init()
            assert app.config['PROFILE_FROM'] == 'environment'

            app = ProfileApp.testing_prep()
            assert app.config['PROFILE_FROM'] == 'environment'

    def test_command_line(self):
        resp = invoke_command(ProfileApp, 'show_profile')
        assert 'config-file-default' in resp.output

    def test_command_invoke_from_testing(self):
        pass
