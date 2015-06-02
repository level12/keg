from __future__ import absolute_import
from __future__ import unicode_literals

from keg.db import db
from keg.contrib.helpers import debug

from keg_apps.db.app import DBApp
import keg_apps.db.model.entities as ents


class TestDebug(object):

    @classmethod
    def setup_class(cls):
        DBApp.testing_prep()

    def test_debug_query(self):
        expected = """SELECT blogs.id, blogs.title \nFROM blogs"""

        query = db.session.query(ents.Blog)
        actual = debug.debug_query(query.statement, db.engine)
        assert actual == expected
