from __future__ import absolute_import
from __future__ import unicode_literals

from keg.app import Keg
import keg_apps.web.views.routing as routing
import keg_apps.web.views.templating as templating


def addkeg(value):
    return '{}Keg'.format(value)


def sayfoo():
    return 'foo'


class WebApp(Keg):
    import_name = __name__
    use_blueprints = [routing.blueprint, templating.blueprint]
    keyring_enabled = False

    template_filters = {'addkeg': addkeg}
    template_globals = {'sayfoo': sayfoo}
