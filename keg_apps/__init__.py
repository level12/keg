from __future__ import absolute_import

import sys


def fix_sys_path():
    """
        When running our apps with python like:

            python keg_apps/cli.py

        `keg_apps/` gets put on the front of sys.path.  So, when other packages, like blazeutils
        call `import logging` keg_apps.logging is imported.

        Fix this situation by simply removing keg_apps from sys.path.  It doesn't need to be there
        for anything we are doing.
    """
    if sys.path[0].endswith('keg_apps'):
        sys.path.pop(0)
