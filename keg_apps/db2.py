from __future__ import absolute_import
from __future__ import print_function

from keg.app import Keg


class DB2App(Keg):
    import_name = __name__
    # Silence the keyring warning messages
    keyring_enabled = False
    db_enabled = True
    db_visit_modules = []
