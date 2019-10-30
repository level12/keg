from __future__ import absolute_import

import flask

from keg.web import BaseView as KegBaseView

blueprint = flask.Blueprint(
    'custom',
    __name__,
    template_folder='../templates/specific-path',
    url_prefix='/tanagra',
)


class BaseView(KegBaseView):
    blueprint = blueprint


class BlueprintTest(BaseView):
    def get(self):
        return self.render()


class BlueprintTest2(BaseView):
    url = '/custom-route'

    def get(self):
        return self.render()
