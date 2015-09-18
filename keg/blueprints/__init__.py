from __future__ import absolute_import

import flask

keg = flask.Blueprint('keg', __name__)


@keg.route('/exception-test')
def exception_test():
    raise Exception('Deliberate exception for testing purposes')


@keg.route('/ping')
def ping():
    return '{} ok'.format(flask.current_app.name)
