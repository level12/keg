from __future__ import absolute_import
from __future__ import unicode_literals

import sys

import flask
from flask._compat import reraise
import pathlib


# sentinal object
class NotGiven(object):
    pass


def ensure_dirs(newdir, mode=NotGiven):
    """
        A "safe" verision of Path.makedir(..., parents=True) that will only create the directory
        if it doesn't already exist.  We also manually create parents so that mode is set
        correctly.  Python docs say that mode is ignored when using Path.mkdir(..., parents=True)
    """
    if mode is NotGiven:
        mode = flask.current_app.config['KEG_DIRS_MODE']
    dpath = pathlib.Path(newdir)
    if dpath.is_dir():
        return
    if dpath.is_file():
        raise OSError("A file with the same name as the desired"
                      " directory, '{}', already exists.".format(dpath))
    ensure_dirs(dpath.parent, mode=mode)
    dpath.mkdir(mode)


def reraise_lastexc():
    exc_type, exc_value, tb = sys.exc_info()
    reraise(exc_type, exc_value, tb)


class classproperty(property):
    """A decorator that behaves like @property except that operates
    on classes rather than instances.
    """
    def __init__(self, fget, *arg, **kw):
        super(classproperty, self).__init__(fget, *arg, **kw)
        self.__doc__ = fget.__doc__

    def __get__(desc, self, cls):
        return desc.fget(cls)
