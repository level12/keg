import logging

from keg.app import Keg


log = logging.getLogger(__name__)


class LoggingApp(Keg):
    import_name = __name__
