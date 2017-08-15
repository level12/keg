from __future__ import absolute_import

import flask
from flask_wtf import FlaskForm
from keg.app import Keg
from wtforms import StringField


class BugApp(Keg):
    import_name = __name__
    keyring_enabled = False


# Has to be a second app b/c the fix depends on a configuration value passed through testing_prep()
# which will only apply once per App class due to how testing.ContextManager works.
class BugFixApp(Keg):
    import_name = __name__
    keyring_enabled = False


class MyForm(FlaskForm):
    name = StringField('name')


@BugApp.route('/form')
@BugFixApp.route('/form')
def form():
    form = MyForm()
    form_tpl = '''
    {{ form.csrf_token }}
    {{ form.name(size=20) }}
    '''
    return flask.render_template_string(form_tpl, form=form)
