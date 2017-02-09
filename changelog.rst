0.4.1 - 2017-02-09
------------------

* BUG: Properly quote pgsql identifiers during create (86852ad_)

.. _86852ad: https://github.com/level12/keg/commit/86852ad



0.4.0 - 2016-12-19
------------------

* BUG: Properly Update Keyring Config Data (7f1908f_)
* MSSQL dialect support (df7e89d_)
* MAINT: Refactor keyring to accept bytes (15bc04b_)
* MAINT: Remove deprecated flask hooks (4f7e2bf_)
* Remove unicode_literal futures (dc2fa85_)
* MAINT: Create windows build environment (983e040_)
* MAINT: Run CI with Docker (bc7a877_)
* Remove extra cp in readme (7e94815_)

.. _7f1908f: https://github.com/level12/keg/commit/7f1908f
.. _df7e89d: https://github.com/level12/keg/commit/df7e89d
.. _15bc04b: https://github.com/level12/keg/commit/15bc04b
.. _4f7e2bf: https://github.com/level12/keg/commit/4f7e2bf
.. _dc2fa85: https://github.com/level12/keg/commit/dc2fa85
.. _983e040: https://github.com/level12/keg/commit/983e040
.. _bc7a877: https://github.com/level12/keg/commit/bc7a877
.. _7e94815: https://github.com/level12/keg/commit/7e94815


0.3.1 released 2016-03-17
-------------------------

- Fixed 0.3.0 build where readme wouldn't install correctly
- Cleaned up repo which had a coverage report commited
- Added a new build environment

0.3.0 released 2015-09-16
-------------------------

- better pypi classifiers
- use `Wheelhouse <https://github.com/level12/wheelhouse>`_ for dependency management
- Add tests for `BaseView` auto-assign feature.
- Add an asset manager.

    * Templates can now use the `assets_include` tag in Jinja templates to
      automatically include the content of a file with the same base name but a 'css' or 'js'
      suffix. See `keg_apps/templating/templates/assets_in_template.html` for example.
    * Templates can now use the `assets_content` tag to include content with a specific suffix.  See
      `keg_apps/templating/templates/assets_content.html` for example.

- Adjust DB clearing so that `prep_empty()` is called after during db_clear() and not
  only `db_init_with_clear().`
- Fix selection of configuration profile so that the ordering is consitent for app instances
  created by `testing_prep()` and `invoke_command()`.

Backwards incompatibility notes:

- In the unlikely event you were relying on `keg.db:DatabaseManager.prep_empty()` in a non-default
  way, you may have some adjustments to make.
- `myapp.config_profile` has been removed.  Use `myapp.config.profile` instead.
- the signature of `MyApp()` and `myapp.init()` has changed.


development version: 2015-05-25
-------------------------------

- Remove `Keg.testing_cleanup()`: wasn't really needed
- Fix db init when SQLALCHEMY_BINDS config option not present but DB feature enabled
- Adjust the way Jinja filters and globals are handled.  Keg will now process `.template_filters` and
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
  implemented by overriding that method on an app and specifying a different DB manager.
- `keg.db.DatabaseManager` is multi-connection aware using the "bind" functionality adopted by
  Flask-SQLAlchemy.
- Added `keg_apps.db` application and related tests.
- Added `keg.db.dialect_ops` to manager RDBMS specific database interactions.
- Move `clear_db()` functionality into `keg.db.dialect_ops`
- Add concept of dialect options to Keg config handling (`KEG_DB_DIALECT_OPTIONS`).  The
  PostgreSQL dialect handles the option `postgresql.schemas` to facilitate the testing setup of
  multiple schemas in a PostgreSQL database.  See `keg_apps.db.config` for example usage.

BC changes required:

- On your app, if you have `sqlalchemy_enabled` set, change it to `db_enabled`
- If importing from `keg.sqlalchemy` change to `keg.db`.
