from __future__ import absolute_import

from keg.app import Keg


class ProfileApp(Keg):
    import_name = 'keg_apps.profile'
    keyring_enabled = False
