from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from keg.app import Keg

log = logging.getLogger(__name__)


class LoggingApp(Keg):
    import_name = __name__
    config_profile = 'TestingProfile'


@LoggingApp.command()
def warn():
    log.info('warning log entry')

