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

- stdout logging

    - default: info level for this app; warning for root logger
    - verbse 1: debug level for this app; warning for root logger
    - verbose 2: debug level for root logger
    - quiet 1: warning level for root logger
    - quiet 2: no logging output to stdout
    - should have second command level flag for easy wildcard filtering of log output

- file logging

    - should have sane defaults for app level logs and error logs
    - files should be stored in OS recommended location
    - app should take care of creating folders hierarchy to log location

- keyring

    - main usage is to avoid putting secret values in config files
    - enabled by default, but should be easily and/or automatically turned off (if insecure)

- configuration

Installation
============

- pip install keg
- pip install keg[testing]  # if you will test your apps according to Keg's assumptions

Keg Development
===============

- Checkout the source code
- pip install -e .
- pip install -e .[development]
- py.test
- flake8
- or, optionally: tox

Questions & Comments
====================

For now, please visit: http://groups.google.com/group/blazelibs

Current Status
==============

Very Alpha, expect changes.


Recent Breaking Changes
=======================

2015-02-10
----------

* Keg() signature chagned to more closely match Flask, 'config_profile' should still work as a
  keyword argument, but is no longer positionally the first argument.
* A Keg instance needs to have .init() called manually after object instantation.  This facilitates
  being able to grab the Keg instance before all the setup work is done, similiar to how Flask
  extensions can usually be instantiated and then .init_app(app) called later.
* pytest setup code should use the new testing_create() method on the app:

    def pytest_configure(config):
        FISResid.testing_create()
