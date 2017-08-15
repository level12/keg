from __future__ import absolute_import

from keg.app import Keg
from keg_apps.web.views import all_blueprints


def addkeg(value):
    return '{}Keg'.format(value)


def sayfoo():
    return 'foo'


class WebApp(Keg):
    import_name = __name__
    use_blueprints = all_blueprints
    keyring_enabled = False

    template_filters = {'addkeg': addkeg}
    template_globals = {'sayfoo': sayfoo}

    def on_init_complete(self):
        # Using .route() in an instance context
        @self.route('/simple3')
        def simple3():
            return 'simple3'


# Using .route() in a class context
@WebApp.route('/simple', endpoint='simple1', methods=['GET', 'POST'])
def simple():
    return 'simple'


@WebApp.route('/simple2', methods=['GET', 'POST'])
def simple2():
    return 'simple2'
