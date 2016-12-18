from __future__ import absolute_import

from keg.app import Keg
from keg_apps.web.views import all_blueprints


def addkeg(value):
    return '{}Keg'.format(value)


def sayfoo():
    return 'foo'


class WebApp(Keg):
    import_name = __name__
    use_blueprints = all_blueprints
    keyring_enabled = False

    template_filters = {'addkeg': addkeg}
    template_globals = {'sayfoo': sayfoo}
