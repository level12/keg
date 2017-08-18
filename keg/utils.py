from __future__ import absolute_import

import os
import sys

import flask
from flask._compat import reraise
import pathlib
from werkzeug.utils import import_string


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
        mode = flask.current_app.config['KEG_DIR_MODE']
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


class ClassProperty(property):
    """A decorator that behaves like @property except that operates
    on classes rather than instances.
    """
    def __init__(self, fget, *arg, **kw):
        self.ignore_set = kw.pop('ignore_set', False)
        self.__doc__ = fget.__doc__
        super(ClassProperty, self).__init__(fget, *arg, **kw)

    def __get__(self, obj, cls):  # noqa
        return self.fget(cls)

    def __set__(self, cls, value):  # noqa
        if self.fset is None and not self.ignore_set:
            raise AttributeError("can't set attribute")
        if not self.ignore_set:
            self.fset(cls, value)


classproperty = ClassProperty


class HybridMethod(object):
    """
        A decorator which allows definition of a Python object method with both
        instance-level and class-level behavior:

            Class Bar:

                @hybridmethod
                def foo(self, rule, **options):
                    # this is used in an instance context

                @foo.classmethod
                def foo(cls, rule, **options):
                    # this is used in class context

    """

    def __init__(self, func, cm_func=None):
        self.instance_func = func
        self.classmethod(cm_func or func)

    def __get__(self, instance, owner):
        if instance is None:
            return self.cm_func.__get__(owner, owner.__class__)
        else:
            return self.instance_func.__get__(instance, owner)

    def classmethod(self, cm_func):
        """Provide a modifying decorator that is used as a classmethod decorator."""

        self.cm_func = cm_func
        if not self.cm_func.__doc__:
            self.cm_func.__doc__ = self.instance_func.__doc__
        return self


hybridmethod = HybridMethod


def pymodule_fpaths_to_objects(fpaths):
    """
        Takes an iterable of file paths reprenting possible python modules and will return an
        iterable of tuples with the file path along with the contents of that file if the file
        exists.
    """
    retval = []
    for fpath in fpaths:
        path = pathlib.Path(fpath)
        if path.exists():
            pymodule_globals = {}
            with open(fpath) as fo:
                exec(compile(fo.read(), fpath, 'exec'), pymodule_globals)
            retval.append((fpath, pymodule_globals))
    return retval


def app_environ_get(app_import_name, key, default=None):
    # App names often have periods and it is not possibe to export an
    # environment variable with a period in it.
    app_name = app_import_name.replace('.', '_').upper()
    environ_key = '{}_{}'.format(app_name, key.upper())

    return os.environ.get(environ_key, default)


def visit_modules(dotted_paths, base_path=None):
    for path in dotted_paths:
        if path.startswith('.') and base_path is not None:
            path = base_path + path
        import_string(path)
