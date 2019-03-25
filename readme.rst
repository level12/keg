.. default-role:: code

Keg: more than Flask
####################

.. image:: https://codecov.io/github/level12/keg/coverage.svg?branch=master
    :target: https://codecov.io/github/level12/keg?branch=master

.. image:: https://img.shields.io/pypi/v/Keg.svg
    :target: https://img.shields.io/pypi/v/Keg.svg

.. image:: https://img.shields.io/pypi/l/keg.svg
    :target: https://img.shields.io/pypi/l/keg.svg

.. image:: https://img.shields.io/pypi/pyversions/keg.svg
    :target: https://img.shields.io/pypi/pyversions/keg.svg

.. image:: https://img.shields.io/pypi/status/Keg.svg
    :target: https://img.shields.io/pypi/status/Keg.svg

.. image:: https://ci.appveyor.com/api/projects/status/wm35hheykxs8851r
    :alt: AppVeyor Build
    :target: https://ci.appveyor.com/project/level12/keg-6gnlh

Keg is an opinionated but flexible web framework built on Flask and SQLAlchemy.


Keg's Goal
==========

The goal for this project is to encapsulate Flask best practices and libraries so devs can avoid
boilerplate and work on the important stuff.

We will lean towards being opinionated on the big things (like SQLAlchemy as our ORM) while
supporting hooks and customizations as much as possible.

Think North of Flask but South of Django.

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

Installation
============

`pip install keg`


App Configuration
=================

CLI Command
-----------

The command `<myapp> develop config` will give detailed information about the files and objects
being used to configure an application.

Profile Priority
----------------

All configuration classes with the name `DefaultProfile` will be applied to the app's config
first.

Then, the configuration classes that match the "selected" profile will be applied on top of the
app's existing configuration. This makes the settings from the "selected" profile override any
settings from the `DefaultProfile.`

Practically speaking, any configuration that applies to the entire app regardless of what context
it is being used in will generally go in `myapp.config` in the `DefaultProfile` class.

Selecting a Configuration Profile
---------------------------------

The "selected" profile is the name of the objects that the Keg configuration handling code will
look for.  It should be a string.

A Keg app considers the "selected" profile as follows:

* If `config_profile` was passed into `myapp.init()` as an argument, use it as the
  selected profile.  The `--profile` cli option uses this method to set the selected profile and
  therefore has the highest priority.
* Look in the app's environment namespace for "CONFIG_PROFILE".  If found, use it.
* If running tests, use "TestProfile".  Whether or not the app is operating in this mode is
  controlled by the use of:

  - `myapp.init(use_test_profile=True)` which is used by `MyApp.testing_prep()`
  - looking in the app's environment namespace for "USE_TEST_PROFILE" which is used by
    `keg.testing.invoke_command()`

* Look in the app's main config file (`app.config`) and all it's other
  config files for the variable `DEFAULT_PROFILE`.  If found, use the value from the file with
  highest priority.


Keg Development
===============

To develop on keg, begin by installing dependencies and running the tests::

    git clone https://github.com/level12/keg keg-src
    cd keg-src

    cp keg_apps/db/user-config-tpl.py ~/.config/keg_apps.db/keg_apps.db-config.py
    # edit the DB connection info in this file (you don't have to use vim):
    vim ~/.config/keg_apps.db/keg_apps.db-config.py

    # Create a virtualenv with a supported python version.  Activate it.
    pip install -e .[tests]
    pytest keg

You can then examine tox.ini for insights into our development process.  In particular, we:

* use `pytest` for testing (and coverage analysis)
* use `flake8` for linting

Preview Readme
--------------

When updating the readme, use `restview --long-description` to preview changes.


Issues & Discussion
====================

Please direct questions, comments, bugs, feature requests, etc. to:
https://github.com/level12/keg/issues

Current Status
==============

* Stable in a relatively small number of production environments.
* API is likely to change with smaller compatibility breaks happening more frequently than larger ones.


Configuration Variables
-----------------------

This is not an exhaustive list of `KEG_` specific configuration variables:

- ``KEG_DB_ENGINE_OPTIONS``: Add additional engine options to the
  ``sqlalchemy.create_engine`` call when working with a database. ::

      KEG_DB_ENGINE_OPTIONS = {
          'json_serializer': flask.json.dumps,
          'json_deserializer': flask.json.loads,
      }
