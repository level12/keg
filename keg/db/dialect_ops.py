from __future__ import absolute_import

from sqlalchemy import MetaData
import six

from ..db import db


class DialectOperations(object):
    dialect_map = {}
    option_defaults = None

    def __init__(self, engine, bind_name, options=None):
        # this engine is tied to a particular "bind" use it instead of db.engine
        self.engine = engine
        self.bind_name = bind_name
        self.assign_options(options or {})

    def assign_options(self, option_pairs):
        if not self.option_defaults:
            return
        for option_key in self.option_defaults.keys():
            full_key = '{}.{}'.format(self.dialect_name, option_key)
            attr_name = 'opt_{}'.format(option_key)
            default_opt_value = self.option_defaults[option_key]
            opt_value = option_pairs.get(full_key, default_opt_value)
            setattr(self, attr_name, opt_value)

    def execute_sql(self, statements):
        for sql in statements:
            self.engine.execute(sql)

    def create_all(self):
        db.create_all(bind=self.bind_name)

    @classmethod
    def create_for(cls, engine, bind_name, options):
        dialect_name = engine.dialect.name
        if dialect_name in cls.dialect_map:
            cls = cls.dialect_map[dialect_name]
            return cls(engine, bind_name, options)
        else:
            raise Exception('DialectOperations does not yet support the "{}" database.'
                            .format(dialect_name))

    def prep_empty(self):
        pass

    def on_connect(self, dbapi_connection, connection_record):
        pass


class PostgreSQLOps(DialectOperations):
    dialect_name = 'postgresql'
    option_defaults = {'schemas': ('public',)}

    def drop_all(self):
        sql = []
        for schema in self.opt_schemas:
            sql.extend([
                'DROP SCHEMA IF EXISTS {} CASCADE;'.format(schema),
            ])
        self.execute_sql(sql)

    def prep_empty(self):
        sql = []
        connection_user = self.engine.url.username
        for schema in self.opt_schemas:
            sql.extend([
                'CREATE SCHEMA {} AUTHORIZATION {};'.format(schema, connection_user),
                'GRANT ALL ON SCHEMA {} TO {};'.format(schema, connection_user),
            ])
        self.execute_sql(sql)

DialectOperations.dialect_map['postgresql'] = PostgreSQLOps


class SQLiteOps(DialectOperations):
    dialect_name = 'sqlite'

    def on_connect(self, dbapi_connection, connection_record):
        # Want SQLite to use foreign keys
        # todo: if this becomes undesirable for some reason, we can make it an option.
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def drop_all(self):
        # drop the views
        sql = "select name from sqlite_master where type='view'"
        rows = self.engine.execute(sql)
        drop_sql = ['drop view {0}'.format(record['name']) for record in rows]
        self.execute_sql(drop_sql)

        # Find all the tables using metadata and reflection.  Use a custom MetaData instance to
        # avoid contaminating the metadata associated with our entities.
        md = MetaData(bind=self.engine)
        md.reflect()
        for table in reversed(md.sorted_tables):
            try:
                self.engine.execute('drop table {}'.format(table.name))
            except Exception as e:
                if 'no such table' not in str(e):
                    raise


DialectOperations.dialect_map['sqlite'] = SQLiteOps


class MicrosoftSQLOps(DialectOperations):
    dialect_name = 'mssql'
    option_defaults = {'schemas': tuple()}

    def drop_all(self):
        # generate drops for all objects, being careful of the schema the object belongs to
        mapping = {
            'P': 'drop procedure [{schema_name}].[{name}]',
            'C': 'alter table [{schema_name}].[{parent_name}] drop constraint [{name}]',
            ('FN', 'IF', 'TF'): 'drop function [{schema_name}].[{name}]',
            'V': 'drop view [{schema_name}].[{name}]',
            'F': 'alter table [{schema_name}].[{parent_name}] drop constraint [{name}]',
            'U': 'drop table [{schema_name}].[{name}]',
        }
        delete_sql = []
        for type, drop_sql in six.iteritems(mapping):
            sql = 'select name, object_name( parent_object_id ) as parent_name '\
                ', OBJECT_SCHEMA_NAME(object_id) as schema_name '\
                'from sys.objects where type in (\'{}\')'.format("', '".join(type))
            rows = self.engine.execute(sql)
            for row in rows:
                delete_sql.append(drop_sql.format(**dict(row)))
        # removing schemas can be tricky. SQL Server 2016+ supports DROP SCHEMA IF EXISTS ...
        #   syntax, but we need to support earlier versions. Technically, an IF EXISTS(...) DROP
        #   SCHEMA should work, but testing shows the drop never happens when executed in this
        #   fashion. So, query sys.schemas directly, and drop any schemas that we are interested
        #   in (according to the bind opts)
        schema_sql = 'select name from sys.schemas'
        rows = self.engine.execute(schema_sql)
        for row in rows:
            if row.name in self.opt_schemas:
                delete_sql.append('drop schema {}'.format(row.name))
        # all drops should be in order, execute them all
        self.execute_sql(delete_sql)

    def prep_empty(self):
        sql = []
        for schema in self.opt_schemas:
            sql.extend([
                'CREATE SCHEMA {}'.format(schema),
            ])
        self.execute_sql(sql)


DialectOperations.dialect_map['mssql'] = MicrosoftSQLOps
