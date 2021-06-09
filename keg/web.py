from __future__ import absolute_import

import inspect
import sys

from blazeutils.strings import case_cw2us, case_cw2dash
import flask
from flask import request
from flask.views import MethodView, MethodViewType, http_method_funcs
import six
from werkzeug.datastructures import MultiDict

from keg.extensions import lazy_gettext as _
from keg.utils import validate_arguments, ArgumentValidationError


class ImmediateResponse(Exception):
    def __init__(self, response):
        self.response = response


def handle_immediate_response(exc):
    return exc.response


def flash_abort(message):
    flask.flash(message, 'error')
    raise ImmediateResponse


def redirect(endpoint, *args, **kwargs):
    if endpoint.upper() == endpoint:
        keg_endpoints = flask.current_app.config['KEG_ENDPOINTS']
        if endpoint.lower() in keg_endpoints:
            endpoint = keg_endpoints[endpoint.lower()]

    resp = flask.redirect(flask.url_for(endpoint, *args, **kwargs))
    raise ImmediateResponse(resp)


class ViewArgumentError(Exception):
    pass


def _werkzeug_multi_dict_conv(md):
    '''
        Werzeug Multi-Dicts are either flat or lists, but we want a single value
        if only one value or a list if multiple values
    '''
    retval = {}
    for key, value in six.iteritems(md.to_dict(flat=False)):
        if len(value) == 1:
            retval[key] = value[0]
        else:
            retval[key] = value
    return retval


def _call_with_expected_args(view, calling_args, method, method_is_bound=True):
    """ handle argument conversion to what the method accepts """
    if isinstance(method, six.string_types):
        if not hasattr(view, method):
            return
        method = getattr(view, method)

    try:
        # validate_arguments is made for a function, not a class method
        # so we need to "trick" it by sending self here, but then
        # removing it before the bound method is called below
        pos_args = (view,) if method_is_bound else tuple()
        args, kwargs = validate_arguments(method, pos_args, calling_args.copy())
    except ArgumentValidationError as e:
        msg = _('Argument mismatch occured: method={method}, missing={missing}, '
                'extra_keys={extra_keys}, extra_pos={extra_pos}.'
                '  Arguments available: {calling_args}',
                method=method, missing=e.missing, extra_keys=e.extra,
                extra_pos=e.extra_positional, calling_args=calling_args)
        raise ViewArgumentError(msg)
    if method_is_bound:
        # remove "self" from args since its a bound method
        args = args[1:]
    return method(*args, **kwargs)


class _ViewMeta(MethodViewType):
    def __init__(cls, name, bases, d):
        MethodViewType.__init__(cls, name, bases, d)

        # Assuming child views will always have a blueprint OR they are intended to be used like
        # abstract classes and will never be routed to directly. Apps/libs will need to call
        # assign_blueprint directly if a blueprint is not set in the view class definition, but
        # the view is intended to receive routes.
        if cls.blueprint is not None:
            cls.assign_blueprint(cls.blueprint)


class BaseView(MethodView, metaclass=_ViewMeta):
    """
    Base class for all Keg views to inherit from. `BaseView` automatically calculates and installs
    routing, templating, and responding methods for HTTP verb named functions.

    .. literalinclude:: /examples/BaseView.py
    """
    blueprint = None
    url = None
    template_name = None
    _index_method = None

    require_authentication = False
    auto_assign = tuple()
    # names of qs arguments that should be merged w/ URL arguments and passed to view methods
    expected_qs_args = []

    def __init__(self, responding_method=None):
        self.responding_method = responding_method

    def calc_responding_method(self):
        if self.responding_method:
            method_name = self.responding_method

            # sometimes the real method name is based on the name of the method combined with the
            # HTTP method/verb.
            method_name_verb = '{}_{}'.format(method_name, request.method.lower())
            if not hasattr(self, method_name) and hasattr(self, method_name_verb):
                method_name = method_name_verb
        else:
            method_name = request.method.lower()

            # If the request method is HEAD and we don't have a handler for it
            # retry with GET.
            if request.method == 'HEAD' and not hasattr(self, 'head'):
                method_name = 'get'

        method_obj = getattr(self, method_name, None)

        assert method_obj is not None, _('Unimplemented method {name}', name=method_name)

        return method_obj

    def dispatch_request(self, **kwargs):
        self.template_args = {}
        calling_args = self.process_calling_args(kwargs)
        self._calling_args = calling_args
        _call_with_expected_args(self, calling_args, 'pre_auth')
        _call_with_expected_args(self, calling_args, 'check_auth')
        _call_with_expected_args(self, calling_args, 'pre_loaders')
        self.call_loaders(calling_args)
        _call_with_expected_args(self, calling_args, 'pre_method')

        method_obj = self.calc_responding_method()
        response = _call_with_expected_args(self, calling_args, method_obj)

        # The following condition is intended to guard against None or no return
        # from the responding method. But, an empty string is a valid response that
        # would fail the falsy test, so check that one specifically.
        if not response and response != '':
            self.process_auto_assign()
            _call_with_expected_args(self, calling_args, 'pre_render')
            response = self.render()
        calling_args['_response'] = response
        pre_response = _call_with_expected_args(self, calling_args, 'pre_response')
        if pre_response is not None:
            return pre_response
        return response

    def process_calling_args(self, urlargs):
        # start with query string arguments that are expected
        args = MultiDict()
        if self.expected_qs_args:
            for k in six.iterkeys(request.args):
                if k in self.expected_qs_args:
                    args.setlist(k, request.args.getlist(k))

        # add URL arguments, replacing GET arguments if they are there.  URL
        # arguments get precedence and we don't want to just .update()
        # because that would allow arbitrary get arguments to affect the
        # values of the URL arguments
        for k, v in six.iteritems(urlargs):
            args[k] = v

        return _werkzeug_multi_dict_conv(args)

    def call_loaders(self, calling_args):
        for attr_name, method_obj in inspect.getmembers(self, inspect.ismethod):
            if not attr_name.endswith('_loader'):
                continue
            arg_key = attr_name[:-7]
            retval = _call_with_expected_args(self, calling_args, method_obj)
            if retval is None:
                flask.abort(404)
            # have to add it to internal variable b/c calling_args is a copy, not the actual object
            self._calling_args[arg_key] = retval

    def check_auth(self):
        pass
        # if self.require_authentication and not current_user.is_authenticated():
        #    flask.abort(401)

    def process_auto_assign(self):
        for key in self.auto_assign:
            self.assign(key, getattr(self, key))

    def calc_class_fname(self):
        return case_cw2us(self.__class__.__name__)

    def calc_template_name(self):
        if self.template_name is not None:
            return self.template_name
        template_path = '{}.html'.format(self.calc_class_fname())
        blueprint_name = request.blueprint
        if blueprint_name:
            template_path = '{}/{}'.format(blueprint_name, template_path)
        return template_path

    def assign(self, key, value):
        self.template_args[key] = value

    def render(self):
        return flask.render_template(self.calc_template_name(), **self.template_args)

    @classmethod
    def calc_url(cls, use_blueprint=True):
        # calc_url will generally return the full url to reach a view. Turn use_blueprint off when
        # setting up the blueprint itself (see init_routes and init_blueprint)
        prefix = (cls.blueprint.url_prefix or '') if cls.blueprint and use_blueprint else ''
        if cls.url is not None:
            return prefix + cls.url
        return prefix + '/' + case_cw2dash(cls.__name__)

    @classmethod
    def calc_endpoint(cls, use_blueprint=True):
        # calc_endpoint will generally return the full endpoint for a view. Turn use_blueprint off
        # when setting up the blueprint itself (see init_routes and init_blueprint)
        prefix = (cls.blueprint.name + '.') if cls.blueprint and use_blueprint else ''
        return prefix + case_cw2dash(cls.__name__)

    @classmethod
    def init_routes(cls):
        cls.url_rules = []
        cls.view_funcs = {}

        def method_with_rules(obj):
            # isroutine() matches functions (PY3) and unbound methods (PY2).
            return inspect.isroutine(obj) and hasattr(obj, '_keg_rules')

        for method_name, method_obj in inspect.getmembers(cls, predicate=method_with_rules):
            for rule, options in method_obj._keg_rules:
                method_route = MethodRoute(method_name, rule, options,
                                           cls.calc_url(use_blueprint=False),
                                           cls.calc_endpoint(use_blueprint=False))
                mr_options = method_route.options()
                if method_route.endpoint not in cls.view_funcs:
                    view_func = cls.as_view(method_route.view_func_name,
                                            method_route.sanitized_method_name('_'))
                    cls.view_funcs[method_route.endpoint] = view_func
                mr_options['view_func'] = cls.view_funcs[method_route.endpoint]
                cls.blueprint.add_url_rule(method_route.rule(), **mr_options)
            if method_name in http_method_funcs and cls.methods:
                # A @route() is being used on a method with the same name as an HTTP verb.
                # Since this method is being explicitly routed, the automatic rule that would
                # be created due to MethodView logic should not apply.
                cls.methods.remove(method_name.upper())

    @classmethod
    def init_blueprint(cls, rules):
        endpoint = cls.calc_endpoint(use_blueprint=False)
        class_url = cls.calc_url(use_blueprint=False)

        if cls.methods:
            # Flask assigns the endpoint to the __name__ atribute of the function it creates and
            # therefore the endpoint must be a `str`.
            str_endpoint = str(endpoint)
            view_func = cls.as_view(str_endpoint)

            absolute_found = False
            for rule, options in rules:
                if rule.startswith('/'):
                    absolute_found = True
                    class_url = rule
                else:
                    rule = '{}/{}'.format(class_url, rule)
                cls.blueprint.add_url_rule(rule, endpoint=endpoint, view_func=view_func, **options)

            if not absolute_found:
                cls.blueprint.add_url_rule(class_url, endpoint=endpoint, view_func=view_func)

        for rule, options in cls.url_rules:
            cls.blueprint.add_url_rule(rule, **options)

    @classmethod
    def assign_blueprint(cls, blueprint):
        if not blueprint:
            raise Exception('blueprint {} could not be assigned'.format(blueprint))

        cls.blueprint = blueprint
        rules = []
        if hasattr(cls, '_rules'):
            rules = cls._rules
            del cls._rules

        cls.init_routes()
        cls.init_blueprint(rules)


class MethodRoute(object):

    def __init__(self, method_name, rule, options, parent_url, parent_endpoint):
        self.method_name = method_name
        self._rule = rule
        # We use destructive operations on options, so make a copy.
        self._options = options.copy()
        self.parent_url = parent_url
        self.parent_endpoint = parent_endpoint

    def sanitized_method_name(self, separator='-'):
        method_identifier = self.method_name.replace('_', separator)

        # method names can be given like foo_get() and foo_post() which indicate the HTTP verb
        # used but shouldn't affect the URL.
        parts = method_identifier.split(separator)
        method_name_suffix = parts[-1]
        if len(parts) > 1 and method_name_suffix in http_method_funcs:
            last_position = (len(method_name_suffix) + 1) * -1
            return method_identifier[:last_position]

        return method_identifier

    @property
    def endpoint(self):
        return '{}:{}'.format(self.parent_endpoint, self.sanitized_method_name())

    @property
    def view_func_name(self):
        return str('{}_{}'.format(self.parent_endpoint, self.sanitized_method_name('_')))

    def rule(self):
        method_url = '{}/{}'.format(self.parent_url, self.sanitized_method_name())

        # Handle no rule given by @route().
        if not self._rule:
            return method_url

        # Handle a relative rule given by @route().
        if not self._rule.startswith('/'):
            return '{}/{}'.format(method_url, self._rule)

        return self._rule

    def options(self):
        self._options['endpoint'] = self.endpoint
        return self._options


def _methods_calc(get, post, post_only, methods):
    if methods is None:
        methods = set()
    else:
        methods = set(methods)

    if get and not post_only:
        methods.add('GET')
    if post or post_only:
        methods.add('POST')

    return methods


def route(rule=None, get=True, post=False, post_only=False, methods=None, **options):
    options['methods'] = _methods_calc(get, post, post_only, methods)

    def wrapper(func):
        if not hasattr(func, '_keg_rules'):
            func._keg_rules = []
        func._keg_rules.append((rule, options))
        return func

    return wrapper


def rule(rule=None, get=True, post=False, post_only=False, methods=None, **options):
    parent_locals = sys._getframe(1).f_locals
    rules = parent_locals.setdefault('_rules', [])
    options['methods'] = _methods_calc(get, post, post_only, methods)
    rules.append((rule, options))
