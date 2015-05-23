Changelog
=========

development version: 2015-05-23
-------------------------------

Making changes to the way database interactions are handled.

- `keg.Keg`'s `sqlalchemy_*` properties have been renamed, see `db_*` variables instead.
- All database management is being delegated to an application specific instance of
  `keg.db.DatabaseManager`.  The class used to manage the db is selected by
  `keg.Keg.db_manager_cls` so custom db management functionality for an app can be easily
  implimented by overriding that method on an app and specifying a different DB manager.
- `keg.db.DatabaseManager` is multi-connection aware using the "bind" functionality adopted by
  Flask-SQLAlchemy.
- Added `keg_apps.db` application and related tests.
- Added `keg.db.dialect_ops` to manager RDBMS specific database interactions.
- Move `clear_db()` functionality into `keg.db.dialect_ops`
- Add concept of dialect options to Keg config handling (`KEG_DB_DIALECT_OPTIONS`).  The
  PostgreSQL dialect handles the option `postgresql.schemas` to facilitate the testing setup of
  multiple schemas in a Postgres database.  See `keg_apps.db.config` for example usage.
