from __future__ import absolute_import
from __future__ import unicode_literals

from keg.app import Keg


class TemplatingApp(Keg):
    import_name = __name__
    keyring_enabled = False
