from __future__ import absolute_import

from collections import defaultdict
import pathlib

from jinja2 import TemplateNotFound
import six


class AssetException(Exception):
    pass


class AssetManager(object):
    """
        A per-request helper object for managing assets related to a request/response cycle.
    """

    def __init__(self, app):
        self.app = app
        self.env = self.app.jinja_env
        self.content = defaultdict(list)

    def load_asset(self, asset_name):
        asset_type = pathlib.Path(asset_name).suffix.lstrip('.')
        try:
            contents, filename, _ = self.env.loader.get_source(self.env, asset_name)
            self.content[asset_type].append((asset_name, filename, contents))
            return True
        except TemplateNotFound:
            return False

    def load_related(self, template_name):
        js_asset_name = six.text_type(pathlib.PurePosixPath(template_name).with_suffix('.js'))
        js_found = self.load_asset(js_asset_name)
        css_asset_name = six.text_type(pathlib.PurePosixPath(template_name).with_suffix('.css'))
        css_found = self.load_asset(css_asset_name)
        if not js_found and not css_found:
            raise AssetException('Could not find related assets for template: {}'
                                 .format(template_name))

    def combine_content(self, asset_type):
        output = []
        for asset_name, filename, contents in self.content[asset_type]:
            comment = '/********************* asset: {} *********************/'.format(asset_name)
            output.append(comment)
            output.append(contents)
        return '\n\n'.join(output)
