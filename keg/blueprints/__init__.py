from __future__ import absolute_import

import flask

from keg.extensions import lazy_gettext as _


keg = flask.Blueprint('keg', __name__)


@keg.route('/exception-test')
def exception_test():
    raise Exception(_('Deliberate exception for testing purposes'))


@keg.route('/ping')
def ping():
    return '{} ok'.format(flask.current_app.name)
