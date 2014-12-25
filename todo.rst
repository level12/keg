ToDo
----------

* make the keyring stuff optional or configurable through configuration file
* log output of keyring setup command is hard to read, I think this is a Flask default
* make keyring commands sub-commands instead of dash commands
* run vs serve command for http server
* standardize help for commands to have either a period or not at the end of the description
* add a testing base class for easily invoking commands, see backupdb test_cli.py
* if a config file has a runtime error, it will be silently ignored
* should we pick up Default objects from system config files?

  * maybe not due to the fact that defaults are defined by the application, if
    a user wants a default, they simply inherit from a parent config?
