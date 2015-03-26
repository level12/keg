from __future__ import absolute_import
from __future__ import unicode_literals

from keg.app import Keg
import keg_apps.web.views.routing as routing
import keg_apps.web.views.templating as templating


class WebApp(Keg):
    import_name = __name__
    use_blueprints = [routing.blueprint, templating.blueprint]
