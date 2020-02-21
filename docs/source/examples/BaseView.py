# Example usage of `keg.web.BaseView`
import flask
from keg.web import BaseView

core_bp = flask.Blueprint('core', __name__)

class FooView(BaseView):
    url = '/foo'
    template_name = 'foo.html'
    blueprint = core_bp

    def get(self):
        context = {
            "bar": "baz",
        }

        return flask.render_template(self.calc_template_name(), **context)

