from __future__ import absolute_import
from __future__ import unicode_literals

import inspect

from blazeutils.strings import case_cw2us, case_cw2dash
import flask
from flask import request
from flask.views import MethodView, MethodViewType
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
        if viewcls.blueprint is not None:
            if not hasattr(viewcls.blueprint, '_keg_views'):
                viewcls.blueprint._keg_views = []
            viewcls.blueprint._keg_views.append(viewcls)
        return viewcls


class PublicView(MethodView):
    __metaclass__ = _ViewMeta

    automatic_route = True
    blueprint = None
    url = None
    urls = []

    require_authentication = False
    auto_assign = tuple()
    # names of qs arguments that should be merged w/ URL arguments and passed to view methods
    expected_qs_args = []

    def dispatch_request(self, **kwargs):
        self.template_args = {}
        calling_args = self.process_calling_args(kwargs)
        self._calling_args = calling_args
        _call_with_expected_args(self, calling_args, 'pre_auth')
        _call_with_expected_args(self, calling_args, 'check_auth')
        _call_with_expected_args(self, calling_args, 'pre_loaders')
        self.call_loaders(calling_args)
        _call_with_expected_args(self, calling_args, 'pre_method')

        if request.is_xhr:
            method_name = 'xhr'
        else:
            method_name = request.method.lower()

        meth = getattr(self, method_name, None)

        # If the request method is HEAD and we don't have a handler for it
        # retry with GET.
        if meth is None and request.method == 'HEAD':
            meth = getattr(self, 'get', None)
        assert meth is not None, 'Unimplemented method %s' % method_name

        response = _call_with_expected_args(self, calling_args, meth)
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
        if self.require_authentication and not current_user.is_authenticated():
            flask.abort(401)

    def process_auto_assign(self):
        for key in self.auto_assign:
            self.assign(key, getattr(self, key))

    def template_name(self):
        template_path = '{}.html'.format(case_cw2us(self.__class__.__name__))
        blueprint_name = request.blueprint
        if blueprint_name:
            template_path = '{}/{}'.format(blueprint_name, template_path)
        return template_path

    def assign(self, key, value):
        self.template_args[key] = value

    def render(self):
        return render_template(self.template_name(), **self.template_args)

    @classmethod
    def calc_url(cls):
        if cls.url is not None:
            return cls.url
        return '/' + case_cw2dash(cls.__name__)

    @classmethod
    def calc_endpoint(cls):
        return case_cw2dash(cls.__name__)

    @classmethod
    def init_blueprint(cls, blueprint):
        view_func = cls.as_view(cls.calc_endpoint())
        if not cls.urls:
            blueprint.add_url_rule(cls.calc_url(), view_func=view_func)
        else:
            for url in cls.urls:
                blueprint.add_url_rule(url, view_func=view_func)
