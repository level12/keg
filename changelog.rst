Changelog
=========


development version: 2015-05-25
-------------------------------

- Remove `Keg.testing_cleanup()`: wasn't really needed
- Fix db init when SQLALCHEMY_BINDS config option not present but DB feature enabled
- Adjust the way jinja filters and globals are handled.  Keg will now process `.template_filters` and
  `.template_globals` (both should be dicts) if defined on an app.
- add signals and commands for database init and clearing
- new `Keg.visit_modules` attribute & related functionality to have Keg load Python modules after
  the app has been setup.

BC changes required:

- if you were using `Keg.testing_cleanup()` explicitly, remove it.
- If using `.jinja_filters` on your app, rename to `.template_filters`

development version: 2015-05-23
-------------------------------

Making changes to the way database interactions are handled.

- Move `keg.sqlalchemy` to `keg.db`
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

BC changes required:

- On your app, if you have `sqlalchemy_enabled` set, change it to `db_enabled`
- If importing from `keg.sqlalchemy` change to `keg.db`.
