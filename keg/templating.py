
import pathlib
import six

from flask.globals import _request_ctx_stack


def _keg_default_template_ctx_processor():
    """Default template context processor.  Injects `assets`.
    """
    reqctx = _request_ctx_stack.top
    rv = {}
    if reqctx is not None:
        rv['assets'] = reqctx.assets
    return rv

from jinja2 import nodes
from jinja2.ext import Extension


class AssetsExtension(Extension):
    # a set of names that trigger the extension.
    tags = set(['assets_include'])

    def __init__(self, environment):
        super(AssetsExtension, self).__init__(environment)

        # add the defaults to the environment
        #environment.extend(
        #    fragment_cache_prefix='',
        #    fragment_cache=None
        #)

    def parse(self, parser):
        # the first token is the token that started the tag.  In our case
        # we only listen to ``'assets_include'`` so this will be a name token with
        # `assets_include` as value.  We get the line number so that we can give
        # that line number to the nodes we create by hand.
        lineno = parser.stream.current.lineno
        stream = parser.stream

        # did asset_include have parameters?
        if stream.look().type == 'block_end':
            args = [nodes.Const(parser.name, lineno=lineno)]
        else:
            #print parser.parse_expression()
            parser.fail('asset_include does not yet support parameters')

        # parse the closing bracket for this asset_include call
        stream.next()
        assert stream.current.type == 'block_end'

        # now return a `CallBlock` node that calls our _import_support
        # helper method on this extension.
        return nodes.CallBlock(self.call_method('_import_support', args),
                               [], [], []).set_lineno(lineno)

    def _import_support(self, template_name, caller):
        """Helper callback."""
        ctx = _request_ctx_stack.top
        ctx.assets.load_related(template_name)

        # have to return empty string to avoid exception about None not being iterable.
        return ''



