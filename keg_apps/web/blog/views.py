from keg.web import BaseView

from . import __component__

component_bp = __component__.create_named_blueprint(__name__)


class Blog(BaseView):
    blueprint = component_bp

    def get(self):
        return self.render()
