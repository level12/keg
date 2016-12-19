from __future__ import absolute_import

import os

import mock

from keg.app import Keg
from keg.config import Config
from keg.testing import invoke_command
from keg_apps.profile.cli import ProfileApp


class TestConfigDefaults(object):

    def test_default_profile(self):
        app = Keg(__name__).init()
        assert app.config.profile is None

        # this key comes from Keg's DefaultProfile
        assert 'KEG_ENDPOINTS' in app.config

    def test_app_params_profile(self):
        app = Keg(__name__).init(config_profile='Foo')
        assert app.config.profile == 'Foo'

    @mock.patch.dict('os.environ', {'TEMPAPP_CONFIG_PROFILE': 'bar'})
    def test_environ_profile(self):
        app = Keg('tempapp').init()
        assert app.config.profile == 'bar'

    def test_profile_from_config_file(self):
        config_file_objs = [('/fake/path', dict(DEFAULT_PROFILE='baz'))]
        config = Config('', {})
        config.init_app(None, __name__, '', False, config_file_objs)
        assert config.profile == 'baz'

    def test_default_config_objects_no_profile(self):
        config = Config('', {})
        config.init_app(None, 'fakeapp', '', False)

        # No profile given, so only the default profiles from Keg and the App should be tried.
        expected = [
            'keg.config.DefaultProfile',
            'fakeapp.config.DefaultProfile'
        ]
        assert config.default_config_locations_parsed() == expected

    def test_default_config_objects_with_profile(self):
        config = Config('', {})

        config.init_app('SomeProfile', 'fakeapp', '', False)

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
        config.init_app(None, 'fakeapp', '', False)
        assert config['KEG_LOG_DPATH'] == config.dirs.user_log_dir
        assert config['KEG_LOG_FNAME'] == 'fakeapp.log'
        assert config['testvalue'] == '{not there}'


class TestProfileLoading(object):

    def test_app_init(self):
        """ Even with an environment set, the explict value passed into init() should override. """
        # the direct setting should override the environment
        kwargs = {'KEG_APPS.PROFILE_CONFIG_PROFILE': 'EnvironmentProfile'}
        with mock.patch.dict(os.environ, **kwargs):
            app = ProfileApp().init(config_profile='AppInitProfile')
        assert app.config['PROFILE_FROM'] == 'app-init'

    def test_config_file_default(self):
        """
            No explicit profile and no environment value results in the default coming from
            configuration profiles.
        """
        app = ProfileApp().init()
        assert app.config['PROFILE_FROM'] == 'config-file-default'

    def test_testing_default(self):
        """
            Make sure the testing profile is used when needed.
        """
        app = ProfileApp().init(use_test_profile=True)
        assert app.config['PROFILE_FROM'] == 'testing-default'

        app = ProfileApp.testing_prep()
        assert app.config['PROFILE_FROM'] == 'testing-default'

    def test_environment(self):
        """
            The environment override should work even when in a testing context.
        """
        kwargs = {'KEG_APPS_PROFILE_CONFIG_PROFILE': 'EnvironmentProfile'}
        with mock.patch.dict(os.environ, **kwargs):
            app = ProfileApp().init()
            assert app.config['PROFILE_FROM'] == 'environment'

            app = ProfileApp().init(use_test_profile=True)
            assert app.config['PROFILE_FROM'] == 'environment'

    def test_invoke_command_for_testing(self):
        """
            Using testing.invoke_command() should use a testing profile by default.
        """
        resp = invoke_command(ProfileApp, 'show_profile')
        assert 'testing-default' in resp.output

    def test_invoke_command_with_environment(self):
        """
            Environement overrides should still take priority for invoke_command() usage.
        """
        resp = invoke_command(ProfileApp, 'show_profile',
                              env={'KEG_APPS_PROFILE_CONFIG_PROFILE': 'EnvironmentProfile'})
        assert 'environment' in resp.output
