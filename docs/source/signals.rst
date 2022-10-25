Signals
=======

As Keg is based on Flask architecture, signals are used to set up and execute callback
methods upon certain events.

Attaching a callback to a signal involves the connect decorator::

    from keg.signals import init_complete

    @init_complete.connect
    def init_navigation(app):
        pass

Take care: some signals fire before an app is fully set up and ready. See the definitions
below for when the signals are fired, and what can be counted upon to be available.


Keg Events
----------

* ``init_complete``

  - All of the app's init tasks have run
  - App's ``on_init_complete`` method has run
  - At this point in the process, it should be safe to assume all app-related objects are present

* ``config_complete``

  - App config has been loaded
  - Config is the first property of the app to be initialized. `app.config` will be available,
    but do not count on anything else.

* ``db_before_import``

  - Database options have been configured, and the app is about to visit modules containing
    entities
  - Config, logging, and error handling have been loaded, but no other extensions, and
    the app's ``visit_modules`` has not yet been processed
  - Some SQLAlchemy metadata attributes, such as naming convention, need to be set prior to
    entities loading. Attaching a method on this signal is an ideal way to set these properties.
  - A common practice with signals is to attach handlers in a separate module, and then list that
    module in the app's visit_modules. This works with many signals, however, the database layer
    gets set up very early in app init to make it available in other steps of the init process.

    - As a result, ``db_before_import`` happens long before visit_modules is processed.
    - Instead, use ``db_before_import`` somewhere that gets loaded at import time for the app (e.g.
      in the module containing the app itself, or something it imports).

  - If customization of the db object, metadata, engine options, etc. is needed, ensure that
    no modules containing entities are imported before the connected callback runs.

* ``testing_run_start``

  - ``app.testing_prep`` has set up necessary context and is about to return the test app
  - Not run during normal operation
  - Provides a hook to inject necessary test objects

* ``db_clear_pre``, ``db_clear_post``, ``db_init_pre``, ``db_init_post``

  - Called during the database initialization process, which occurs in test setup and from CLI
    commands
