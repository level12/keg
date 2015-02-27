from __future__ import absolute_import
from __future__ import unicode_literals

import inspect

from blazeutils.strings import case_cw2us, case_cw2dash, simplify_string
import flask
from flask import request
from flask.views import MethodView, MethodViewType, http_method_funcs
from werkzeug.datastructures import MultiDict
from werkzeug.utils import validate_arguments, ArgumentValidationError


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
    for key, value in md.to_dict(flat=False).iteritems():
        if len(value) == 1:
            retval[key] = value[0]
        else:
            retval[key] = value
    return retval


def _call_with_expected_args(view, calling_args, method, method_is_bound=True):
    """ handle argument conversion to what the method accepts """
    if isinstance(method, basestring):
        if not hasattr(view, method):
            return
        method = getattr(view, method)

    try:
        # validate_arguments is made for a function, not a class method
        # so we need to "trick" it by sending self here, but then
        # removing it before the bound method is called below
        pos_args = (view,) if method_is_bound else tuple()
        args, kwargs = validate_arguments(method, pos_args, calling_args.copy())
    except ArgumentValidationError, e:
        msg = 'Argument mismatch occured: method=%s, missing=%s, extra_keys=%s, extra_pos=%s.' \
              '  Arguments available: %s' % (method, e.missing, e.extra, e.extra_positional,
                                             calling_args)
        raise ViewArgumentError(msg)
        # used to raise a BadRequest here, but after deliberation, it seems likely this is only
        # going to happen b/c of programmer error.  Therefore, just propogate the exception.
        raise
    if method_is_bound:
        # remove "self" from args since its a bound method
        args = args[1:]
    return method(*args, **kwargs)


class _ViewMeta(MethodViewType):

    def __new__(cls, clsname, bases, attr):
        viewcls = super(_ViewMeta, cls).__new__(cls, clsname, bases, attr)
        viewcls.init_routes()
        if viewcls.blueprint is not None:
            viewcls.init_blueprint()
        return viewcls


class BaseView(MethodView):
    __metaclass__ = _ViewMeta

    automatic_route = True
    blueprint = None
    url = None
    url_rules = None
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
        elif request.is_xhr:
            method_name = 'xhr'
        else:
            method_name = request.method.lower()
            if method_name == 'get' and self._index_method is not None:
                    method_name = self._index_method

        method_obj = getattr(self, method_name, None)

        # If the request method is HEAD and we don't have a handler for it
        # retry with GET.
        if method_obj is None and request.method == 'HEAD':
            method_obj = getattr(self, 'get', None)

        assert method_obj is not None, 'Unimplemented method %s' % method_name

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

        if not response:
            self.process_auto_assign()
            _call_with_expected_args(self, calling_args, 'pre_render')
            response = self.render()
        calling_args['_response'] = response
        _call_with_expected_args(self, calling_args, 'pre_response')
        return response

    def process_calling_args(self, urlargs):
        # start with query string arguments that are expected
        args = MultiDict()
        if self.expected_qs_args:
            for k in request.args.iterkeys():
                if k in self.expected_qs_args:
                    args.setlist(k, request.args.getlist(k))

        # add URL arguments, replacing GET arguments if they are there.  URL
        # arguments get precedence and we don't want to just .update()
        # because that would allow arbitrary get arguments to affect the
        # values of the URL arguments
        for k, v in urlargs.iteritems():
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

    def calc_template_name(self):
        if self.template_name is not None:
            return self.template_name
        template_path = '{}.html'.format(case_cw2us(self.__class__.__name__))
        blueprint_name = request.blueprint
        if blueprint_name:
            template_path = '{}/{}'.format(blueprint_name, template_path)
        return template_path

    def assign(self, key, value):
        self.template_args[key] = value

    def render(self):
        return flask.render_template(self.calc_template_name(), **self.template_args)

    @classmethod
    def calc_url(cls):
        if cls.url is not None:
            return cls.url
        return '/' + case_cw2dash(cls.__name__)

    @classmethod
    def calc_endpoint(cls):
        return case_cw2dash(cls.__name__)

    @classmethod
    def init_routes(cls):
        if cls.url_rules is None:
            cls.url_rules = []

        def method_with_rules(obj):
            return inspect.ismethod(obj) and hasattr(obj, '_rule_options')

        for name, method_obj in inspect.getmembers(cls, predicate=method_with_rules):
            options = method_obj._rule_options
            dashed_name = case_cw2dash(name)
            class_url = cls.calc_url()
            default_rule = '{}/{}'.format(class_url, dashed_name)

            # if this method is named after an http method, then we assume the method is routing
            # for the class and is not an additional route for the class
            if name in http_method_funcs:
                default_rule = class_url

            if options.pop('index', None):
                assert cls._index_method is None, 'More than one route method has been specified' \
                    ' as the index.'
                cls._index_method = name
                # if this is the index method, than it responds to the class' URL
                default_rule = class_url
            rule = options.pop('rule')
            if not rule:
                rule = default_rule
            elif not rule.startswith('/'):
                # since there is no slash, it is a relative URL
                rule = '{}/{}'.format(default_rule, rule)
            class_endpoint = cls.calc_endpoint()
            method_endpoint = '{}:{}'.format(class_endpoint, dashed_name)
            method_endpoint = options.setdefault('endpoint', method_endpoint)
            view_func_name = simplify_string(method_endpoint.replace(':', '_'), replace_with='_')
            options['view_func'] = cls.as_view(view_func_name.encode('ascii'), name)
            cls.url_rules.append((rule, options))

    @classmethod
    def init_blueprint(cls):
        endpoint = cls.calc_endpoint()
        view_func = cls.as_view(endpoint)
        if cls.methods:
            cls.blueprint.add_url_rule(cls.calc_url(), endpoint=endpoint, view_func=view_func)
        for rule, options in cls.url_rules:
            cls.blueprint.add_url_rule(rule, **options)


def route(rule=None, get=True, post=False, methods=[], **options):
    if get and 'GET' not in methods:
        methods.append('GET')
    if post and 'POST' not in methods:
        methods.append('POST')

    options['methods'] = methods
    options['rule'] = rule

    def wrapper(func):
        func._rule_options = options
        return func

    return wrapper
