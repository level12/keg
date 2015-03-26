from __future__ import absolute_import
from __future__ import unicode_literals

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


def with_metaclass(meta, *bases):
    # This requires a bit of explanation: the basic idea is to make a
    # dummy metaclass for one level of class instantiation that replaces
    # itself with the actual metaclass.  Because of internal type checks
    # we also need to make sure that we downgrade the custom metaclass
    # for one level to something closer to type (that's why __call__ and
    # __init__ comes back from type etc.).
    #
    # This has the advantage over six.with_metaclass in that it does not
    # introduce dummy classes into the final MRO.
    #
    # copied from Flask._compat
    class metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__

        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)
    return metaclass(str('temporary_class'), None, {})
