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
