Features
========

Default Logging Configuration
-----------------------------

We highly recommend good logging practices and, as such, a Keg application does basic setup of the
Python logging system:

- Sets the log level on the root logger to INFO
- Creates two handlers and assigns them to the root logger:

  - outputs to stderr
  - outputs to syslog

- Provides an optional json formatter

The thinking behind that is:

- In development, a developer will see log messages on stdout and doesn't have to monitor a file.
- Log messages will be in syslog by default and available for review there if no other action is
  taken by the developer or sysadmin.  This avoids the need to manage log placement, permissions,
  rotation, etc.
- It's easy to configure syslog daemons to forward log messages to different files or remote log
  servers and it's better to handle that type of need at the syslog level than in the app.
- Structured log files (json) provide metadata details in a easy-to-parse format and should be
  easy to generate.
- The options and output should be easily configurable from the app to account for different needs
  in development and deployed scenarios.
- Keg's logging setup should be easy to turn off and/or completely override for situations where it
  hurts more than it helps.
