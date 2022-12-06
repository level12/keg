# flask.globals.request_ctx is only available in Flask >= 2.2.0
try:
    from flask.globals import request_ctx
except ImportError:
    from flask.globals import _request_ctx_stack
    request_ctx = None

from keg.extensions import lazy_gettext as _


def _get_bc_request_context():
    """Flask 2.2 changed the method of fetching the request context
    from globals. Flask 2.3 will remove the old way of doing it.
    Support both here."""
    if request_ctx is None:
        return _request_ctx_stack.top
    return request_ctx


def _keg_default_template_ctx_processor():
    """Default template context processor.  Injects `assets`.
    """
    reqctx = _get_bc_request_context()
    rv = {}
    if reqctx:
        rv['assets'] = reqctx.assets
    return rv

from jinja2 import nodes  # noqa
from jinja2.ext import Extension  # noqa


class AssetsExtension(Extension):
    # a set of names that trigger the extension.
    tags = set(['assets_include', 'assets_content'])

    def __init__(self, environment):
        super(AssetsExtension, self).__init__(environment)

    def parse(self, parser):
        lineno = parser.stream.current.lineno
        stream = parser.stream

        if stream.current.value == 'assets_include':
            return self.parse_include(parser, stream, lineno)
        return self.parse_content(parser, stream, lineno)

    def parse_include(self, parser, stream, lineno):

        # did asset_include have parameters?
        if stream.look().type == 'block_end':
            args = [nodes.Const(parser.name, lineno=lineno)]
        else:
            # print parser.parse_expression()
            parser.fail(_('asset_include does not yet support parameters'))

        # parse the closing bracket for this asset_include call
        next(stream)
        assert stream.current.type == 'block_end'

        # now return a `CallBlock` node that calls our _import_support
        # helper method on this extension.
        return nodes.CallBlock(self.call_method('_include_support', args),
                               [], [], []).set_lineno(lineno)

    def _include_support(self, template_name, caller):
        """Helper callback."""
        ctx = _get_bc_request_context()
        ctx.assets.load_related(template_name)

        # have to return empty string to avoid exception about None not being iterable.
        return ''

    def parse_content(self, parser, stream, lineno):
        # move from the current Name token to the next token in the stream, which should be the
        # first argument to asset_content tag.
        next(stream)

        # parse the expression
        args = [parser.parse_expression()]

        # now return a `CallBlock` node that calls our support
        # helper method on this extension.
        return nodes.CallBlock(self.call_method('_content_support', args),
                               [], [], []).set_lineno(lineno)

    def _content_support(self, asset_type, caller):
        """Helper callback."""
        ctx = _get_bc_request_context()
        return ctx.assets.combine_content(asset_type)
