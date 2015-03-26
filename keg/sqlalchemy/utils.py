from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from ..sqlalchemy import db
import six

log = logging.getLogger(__name__)


def clear_db():
    dialect_name = db.engine.dialect.name
    if dialect_name == 'postgresql':
        sql = []
        sql.append('DROP SCHEMA public cascade;')
        sql.append('CREATE SCHEMA public AUTHORIZATION {0};'.format(db.engine.url.username))
        sql.append('GRANT ALL ON SCHEMA public TO {0};'.format(db.engine.url.username))
        sql.append('GRANT ALL ON SCHEMA public TO public;')
        sql.append("COMMENT ON SCHEMA public IS 'standard public schema';")
        for exstr in sql:
            try:
                db.engine.execute(exstr)
            except Exception as e:
                log.warn(str(e))
    elif dialect_name == 'sqlite':
        # drop the views
        sql = "select name from sqlite_master where type='view'"
        rows = db.engine.execute(sql)
        # need to get all views before start to try and delete them, otherwise
        # we will get "database locked" errors from sqlite
        records = rows.fetchall()
        for row in records:
            db.engine.execute('drop view {0}'.format(row['name']))

        # drop the tables
        db.metadata.reflect(bind=db.engine)
        for table in reversed(db.metadata.sorted_tables):
            try:
                table.drop(db.engine)
            except Exception as e:
                if 'no such table' not in str(e):
                    raise
    elif dialect_name == 'mssql':
        mapping = {
            'P': 'drop procedure [{name}]',
            'C': 'alter table [{parent_name}] drop constraint [{name}]',
            ('FN', 'IF', 'TF'): 'drop function [{name}]',
            'V': 'drop view [{name}]',
            'F': 'alter table [{parent_name}] drop constraint [{name}]',
            'U': 'drop table [{name}]',
        }
        delete_sql = []
        for type, drop_sql in six.iteritems(mapping):
            sql = 'select name, object_name( parent_object_id ) as parent_name '\
                'from sys.objects where type in (\'{0}\')'.format("', '".join(type))
            rows = db.engine.execute(sql)
            for row in rows:
                delete_sql.append(drop_sql.format(**dict(row)))
        for sql in delete_sql:
            db.engine.execute(sql)
    else:
        raise Exception('clear_db() does not yet support the "{}" database.'.format(dialect_name))
