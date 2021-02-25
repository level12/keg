from __future__ import absolute_import

import flask

from keg.web import BaseView as KegBaseView

blueprint = flask.Blueprint('other', __name__)


class BaseView(KegBaseView):
    blueprint = blueprint


class AutoAssign(BaseView):
    auto_assign = ('bar', 'baz')

    def get(self):
        self.bar = 'bar'
        self.baz = 'baz'
        self.foo = 'foo'


class AutoAssignWithResponse(BaseView):
    auto_assign = ('bar',)
    template_name = 'other/auto_assign.html'

    def get(self):
        self.bar = 'bar'
        return self.render()


class BlankView(BaseView):

    def get(self):
        return ''


class ResponseMiddleware(BaseView):
    url = '/response-middleware/<string:name>'

    def pre_response(self, _response):
        if _response == 'bar':
            return None
        if _response == 'baz':
            return ''
        return _response + '_test'

    def get(self, name):
        return name
