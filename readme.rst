.. default-role:: code

Keg: more than Flask
####################


.. image:: https://coveralls.io/repos/level12/keg/badge.svg?branch=master
    :target: https://coveralls.io/r/level12/keg?branch=master

.. image:: https://codecov.io/github/level12/keg/coverage.svg?branch=master
    :target: https://codecov.io/github/level12/keg?branch=master

.. image:: https://img.shields.io/pypi/dm/Keg.svg
    :target: https://img.shields.io/pypi/dm/Keg.svg

.. image:: https://img.shields.io/pypi/v/Keg.svg
    :target: https://img.shields.io/pypi/v/Keg.svg

.. image:: https://img.shields.io/pypi/l/keg.svg
    :target: https://img.shields.io/pypi/l/keg.svg

.. image:: https://img.shields.io/pypi/pyversions/keg.svg
    :target: https://img.shields.io/pypi/pyversions/keg.svg

.. image:: https://img.shields.io/pypi/status/Keg.svg
    :target: https://img.shields.io/pypi/status/Keg.svg

.. image:: https://badges.gitter.im/level12/keg.svg
    :alt: Join the chat at https://gitter.im/level12/keg
    :target: https://gitter.im/level12/keg?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

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

Coming (maybe not so) soon.  :)

Installation
============

- pip install keg


App Configuration
=================

CLI Command
-----------

The command `<myapp> develop config` will give detailed information about the files and objects
being used to configure an application.

Profile Prority
---------------

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

To develop on keg, begin by running our tests::

    git clone https://github.com/level12/keg keg-src
    cd keg-src
    cp keg_apps/db/user-config-tpl.py ~/.config/keg_apps.db/keg_apps.db-config.py
    # edit the DB connection info in this file (you don't have to use vim):
    vim ~/.config/keg_apps.db/keg_apps.db-config.py
    tox

You can then examine tox.ini for insights into our development process.  In particular, we:

* use `py.test` for testing (and coverage analysis)
* use `flake8` for linting
* store `pip` requirements files in `requirements/`
* cache wheels in `requirements/wheelhouse` for faster & more reliable CI builds

Dependency Management
---------------------

Adding a dependency involves:

#. Adding the dependency to one of the requirements files in `requirements/`.
#. Running `wheelhouse build`

Preview Readme
--------------

When updating the readme, use `restview --long-description` to preview changes.


Issues & Discussion
====================

Please direct questions, comments, bugs, feature requests, etc. to:
https://github.com/level12/keg/issues

Current Status
==============

Very Alpha, expect changes.

