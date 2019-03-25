from __future__ import absolute_import

import six

from blazeutils.strings import simplify


def object_from_source(fpath, objname):
    if six.PY2:
        import imp
        module_name = 'keg_{}'.format(simplify(fpath))
        tmpmodule = imp.load_source(module_name, fpath)
        if not hasattr(tmpmodule, objname):
            return None
        return getattr(tmpmodule, objname)
