from __future__ import absolute_import
from __future__ import unicode_literals

from keg.db import db

import keg_apps.db.model.entities as ents
from keg_apps.db.app import DBApp


def setup_module(module):
    DBApp.testing_prep()


class TestDB(object):

    def test_primary_db_entity(self):
        assert ents.Blog.query.count() == 0
        blog = ents.Blog(title='foo')
        db.session.add(blog)
        db.session.commit()
        assert ents.Blog.query.count() == 1

    def test_postgres_bind_db_entity(self):
        assert ents.PGDud.query.count() == 0
        dud = ents.PGDud(name='foo')
        db.session.add(dud)
        db.session.commit()
        assert ents.PGDud.query.count() == 1

    def test_postgres_db_enttity_alt_schema(self):
        assert ents.PGDud2.query.count() == 0
        dud = ents.PGDud2(name='foo')
        db.session.add(dud)
        db.session.commit()
        assert ents.PGDud2.query.count() == 1
