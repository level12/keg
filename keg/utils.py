from __future__ import absolute_import

import inspect
import os
import weakref

import flask
import pathlib
from werkzeug.utils import import_string

from keg.extensions import lazy_gettext as _

_signature_cache = weakref.WeakKeyDictionary()


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
        raise OSError(_("A file with the same name as the desired"
                        " directory, '{dpath}', already exists.", dpath=dpath))

    ensure_dirs(dpath.parent, mode=mode)
    dpath.mkdir(mode)


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
            raise AttributeError(_("can't set attribute"))
        if not self.ignore_set:
            self.fset(cls, value)


classproperty = ClassProperty


class HybridMethod(object):
    """
    A decorator which allows definition of a Python object method with both
    instance-level and class-level behavior::

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

        If the file does not exist or cannot be accessed, the third term of the tuple stores
        the exception.
    """
    retval = []
    for fpath in fpaths:
        try:
            pymodule_globals = {}
            with open(fpath) as fo:
                exec(compile(fo.read(), fpath, 'exec'), pymodule_globals)
            retval.append((fpath, pymodule_globals, None))
        except (FileNotFoundError, IsADirectoryError, PermissionError) as exc:
            retval.append((fpath, None, exc))
    return retval


def app_environ_get(app_import_name, key, default=None):
    # App names often have periods and it is not possible to export an
    # environment variable with a period in it.
    app_name = app_import_name.replace('.', '_').upper()
    environ_key = '{}_{}'.format(app_name, key.upper())

    return os.environ.get(environ_key, default)


def visit_modules(dotted_paths, base_path=None):
    for path in dotted_paths:
        if path.startswith('.') and base_path is not None:
            path = base_path + path
        import_string(path)


def validate_arguments(func, args, kwargs, drop_extra=True):  # type: ignore
    """Checks if the function accepts the arguments and keyword arguments.
    Returns a new ``(args, kwargs)`` tuple that can safely be passed to
    the function without causing a `TypeError` because the function signature
    is incompatible.  If `drop_extra` is set to `True` (which is the default)
    any extra positional or keyword arguments are dropped automatically.

    The exception raised provides three attributes:

    `missing`
        A set of argument names that the function expected but where
        missing.

    `extra`
        A dict of keyword arguments that the function can not handle but
        where provided.

    `extra_positional`
        A list of values that where given by positional argument but the
        function cannot accept.

    This can be useful for decorators that forward user submitted data to
    a view function::

        from werkzeug.utils import ArgumentValidationError, validate_arguments

        def sanitize(f):
            def proxy(request):
                data = request.values.to_dict()
                try:
                    args, kwargs = validate_arguments(f, (request,), data)
                except ArgumentValidationError:
                    raise BadRequest('The browser failed to transmit all '
                                     'the data expected.')
                return f(*args, **kwargs)
            return proxy

    :param func: the function the validation is performed against.
    :param args: a tuple of positional arguments.
    :param kwargs: a dict of keyword arguments.
    :param drop_extra: set to `False` if you don't want extra arguments
                       to be silently dropped.
    :return: tuple in the form ``(args, kwargs)``.

    .. deprecated:: 2.0
        Will be removed in Werkzeug 2.1. Use :func:`inspect.signature`
        instead.

    Copied from Werkzeug
    """
    parser = _parse_signature(func)
    args, kwargs, missing, extra, extra_positional = parser(args, kwargs)[:5]
    if missing:
        raise ArgumentValidationError(tuple(missing))
    elif (extra or extra_positional) and not drop_extra:
        raise ArgumentValidationError(None, extra, extra_positional)
    return tuple(args), kwargs


def _parse_signature(func):  # type: ignore
    """Return a signature object for the function.

    .. deprecated:: 2.0
        Will be removed in Werkzeug 2.1 along with ``utils.bind`` and
        ``validate_arguments``.
    """
    # if we have a cached validator for this function, return it
    parse = _signature_cache.get(func)
    if parse is not None:
        return parse

    # inspect the function signature and collect all the information
    tup = inspect.getfullargspec(func)
    positional, vararg_var, kwarg_var, defaults = tup[:4]
    defaults = defaults or ()
    arg_count = len(positional)
    arguments = []
    for idx, name in enumerate(positional):
        if isinstance(name, list):
            raise TypeError(
                "cannot parse functions that unpack tuples in the function signature"
            )
        try:
            default = defaults[idx - arg_count]
        except IndexError:
            param = (name, False, None)
        else:
            param = (name, True, default)
        arguments.append(param)
    arguments = tuple(arguments)

    def parse(args, kwargs):  # type: ignore
        new_args = []
        missing = []
        extra = {}

        # consume as many arguments as positional as possible
        for idx, (name, has_default, default) in enumerate(arguments):
            try:
                new_args.append(args[idx])
            except IndexError:
                try:
                    new_args.append(kwargs.pop(name))
                except KeyError:
                    if has_default:
                        new_args.append(default)
                    else:
                        missing.append(name)
            else:
                if name in kwargs:
                    extra[name] = kwargs.pop(name)

        # handle extra arguments
        extra_positional = args[arg_count:]
        if vararg_var is not None:
            new_args.extend(extra_positional)
            extra_positional = ()
        if kwargs and kwarg_var is None:
            extra.update(kwargs)
            kwargs = {}

        return (
            new_args,
            kwargs,
            missing,
            extra,
            extra_positional,
            arguments,
            vararg_var,
            kwarg_var,
        )

    _signature_cache[func] = parse
    return parse


class ArgumentValidationError(ValueError):
    """Raised if :func:`validate_arguments` fails to validate

    .. deprecated:: 2.0
        Will be removed in Werkzeug 2.1 along with ``utils.bind`` and
        ``validate_arguments``.
    """

    def __init__(self, missing=None, extra=None, extra_positional=None):  # type: ignore
        self.missing = set(missing or ())
        self.extra = extra or {}
        self.extra_positional = extra_positional or []
        super().__init__(
            "function arguments invalid."
            f" ({len(self.missing)} missing,"
            f" {len(self.extra) + len(self.extra_positional)} additional)"
        )
