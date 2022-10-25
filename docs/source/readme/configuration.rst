App Configuration
=================

Configuration Variables
-----------------------

- ``KEG_DB_DIALECT_OPTIONS``: Dict of options to provide to the db manager. E.g. "postgresql.schemas".
- ``KEG_DIR_MODE``: Mode used by ``ensure_dirs``. Default 0o777.
- ``KEG_ENDPOINTS``: Keys/endpoints usable via ``keg.web.redirect``.
- ``KEG_LOG_AUTO_CLEAR_HANDLERS``: Remove existing handlers before creating new ones. Default True.
- ``KEG_LOG_JSON_FORMAT_STR``: Format string to use for JSON log output (option for syslog)
- ``KEG_LOG_JSON_FORMATTER_KWARGS``: Args to provide to JSON formatter
- ``KEG_LOG_LEVEL``: Default log level, defaults to INFO and can be modified with CLI options
- ``KEG_LOG_MANAGED_LOGGERS``: Keg creates loggers for these paths. Defaults to no paths
- ``KEG_LOG_STDOUT_FORMAT_STR``: Format string to use for stdout log output
- ``KEG_LOG_STREAM_ENABLED``: Directs Keg to set up a StreamHandler. Default True.
- ``KEG_LOG_SYSLOG_ENABLED``: Directs Keg to set up a SysLogHandler. Default True.
- ``KEG_LOG_SYSLOG_FORMAT_STR``: Format string to use for syslog log output
- ``KEG_LOG_SYSLOG_IDENT``: Log ident for syslog. Defaults to "<app_import_name>.app"
- ``KEG_LOG_SYSLOG_JSON``: Directs Keg to output to syslog with JSON. Default False.
- ``KEG_LOG_SYSLOG_JSON_PREFIX``: Prefix to set in JSON output. Default "@cee:"
- ``KEG_REGISTERED_COMPONENTS``: List of paths to import as component extensions
- ``KEG_SQLITE_ENABLE_FOREIGN_KEYS``: Configure SQLite to enforce foreign keys by default

CLI Command
-----------

The command ``<myapp> develop config`` will give detailed information about the files and objects
being used to configure an application.

Profile Priority
----------------

All configuration classes with the name ``DefaultProfile`` will be applied to the app's config
first.

Then, the configuration classes that match the "selected" profile will be applied on top of the
app's existing configuration. This makes the settings from the "selected" profile override any
settings from the ``DefaultProfile``.

Practically speaking, any configuration that applies to the entire app regardless of what context
it is being used in will generally go in ``myapp.config`` in the ``DefaultProfile`` class.

Selecting a Configuration Profile
---------------------------------

The "selected" profile is the name of the objects that the Keg configuration handling code will
look for.  It should be a string.

A Keg app considers the "selected" profile as follows:

* If ``config_profile`` was passed into ``myapp.init()`` as an argument, use it as the
  selected profile.  The ``--profile`` cli option uses this method to set the selected profile and
  therefore has the highest priority.
* Look in the app's environment namespace for "CONFIG_PROFILE".  If found, use it.
* If running tests, use "TestProfile".  Whether or not the app is operating in this mode is
  controlled by the use of:

  - ``myapp.init(use_test_profile=True)`` which is used by ``MyApp.testing_prep()``
  - looking in the app's environment namespace for "USE_TEST_PROFILE" which is used by
    ``keg.testing.invoke_command()``

* Look in the app's main config file (``app.config``) and all it's other
  config files for the variable ``DEFAULT_PROFILE``.  If found, use the value from the file with
  highest priority.
