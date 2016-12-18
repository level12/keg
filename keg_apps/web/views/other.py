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
