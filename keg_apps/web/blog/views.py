from keg.web import BaseView

from . import __component__

component_bp = __component__.get_named_blueprint(__name__)


class Blog(BaseView):
    blueprint = component_bp

    def get(self):
        return self.render()
