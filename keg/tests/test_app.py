from __future__ import absolute_import
from __future__ import unicode_literals

from blazeutils.testing import raises

from keg.app import Keg, KegAppError


class TestInit(object):

    @raises(KegAppError, 'init() already called')
    def test_init_called_twice_error(self):
        app = Keg(__name__)
        app.init()
        app.init()
