from __future__ import absolute_import

from flask.ctx import RequestContext
from keg.assets import AssetManager


class KegRequestContext(RequestContext):

    def __init__(self, app, environ, request=None):
        super(KegRequestContext, self).__init__(app, environ, request)
        self.assets = AssetManager(app)
