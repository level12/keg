ToDo
#####

* change the way VERSION is handled
* it would be nice if you could setup a custom sqlalchemy manager instead of having to use
  KegSQLAlchemy.  maybe having a register_manager_class() method that replaced the global variable?
* I removed the create_app() classmethod and decided to just do all that work on init.  However,
  that takes away the abililty to get ahold of an instance of the app before doing all the init()
  work.  That may not be ideal, consider how flask extensions often split the creation of the
  class and then use init_app() for setup.

Configuration
-------------

* if a config file has a runtime error, it will be silently ignored
* KEG_DIRS_MODE - should not be set by default.  Let current umask apply unless explicit override.

Logging
--------

* log output of keyring setup command is hard to read, I think this is a Flask default
* yes Flask default log formatting for INFO is too busy


CLI
-----------

* Running an unknown command results in "AttributeError: <app> object has no attribute 'cli'" exception
* run vs serve command for http server
* standardize help for commands to have either a period or not at the end of the description
* there are problems with CLI tests if commands don't get added to the app.  This can happen if
  you have a test that imports the app from .app instead of .cli. We need to automatically visit
  app.cli modules to avoid this...but when would you do that?
* reorganize the default commands so they are more usable for non-web contexts?

  * put all diagnostic commands under a group?
  * put all web commands under a group?  Optionally allow disabling this group from being listed
    for when the app is a CLI only app.

* right now, we hard-code the test profile in conftest.pytest_configure()...verify this can be
  overriden with an environment variable.  Also, integrate with py.test command line to give a
  "--appname-profile = Foo" option so we can run tests against a different test profile if needed.
