.. default-role:: code

Keg: more than Flask
####################


.. image:: https://travis-ci.org/level12/keg.svg?branch=master
    :target: https://travis-ci.org/level12/keg

.. image:: https://coveralls.io/repos/level12/keg/badge.svg?branch=master
    :target: https://coveralls.io/r/level12/keg?branch=master

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

Keg Development
===============

To develop on keg, begin by running our tests::

    git clone https://github.com/level12/keg keg-src
    cd keg-src
    cp cp keg_apps/db/user-config-tpl.py ~/.config/keg_apps.db/keg_apps.db-config.py
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

