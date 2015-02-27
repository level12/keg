from __future__ import absolute_import
from __future__ import unicode_literals

from keg.app import Keg
from .views import public_blueprint


class WebApp(Keg):
    import_name = __name__
    use_blueprints = [public_blueprint]
