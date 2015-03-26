from __future__ import absolute_import
from __future__ import unicode_literals
import flask

from keg.web import BaseView

blueprint = flask.Blueprint('templating', __name__)


class BaseView(BaseView):
    blueprint = blueprint


class Template1(BaseView):
    def get(self):
        self.assign('name', 'world')


class Template2(BaseView):
    template_name = 'templating/template-two.html'

    def get(self):
        pass
