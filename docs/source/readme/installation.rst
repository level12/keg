Installation
============

``pip install keg``


Upgrade Notes
=============

While we attempt to preserve backward compatibility, some Keg versions do introduce
breaking changes. This list should provide information on needed app changes.

- 0.10.0

  - ``rule``: default class view route no longer generated when any rules are present

    - Absolute route had been provided automatically from the class name, but in some situations
      this would not be desired. Views that still need that route can use a couple of solutions:

      - Provide an absolute route rule: ``rule('/my-route')``
      - Use an empty relative route rule: ``rule()``

    - All of an app's routes may be shown on CLI with the ``<app> develop routes`` command

  - Removed ``keg`` blueprint along with ``ping`` and ``exception-test`` routes
  - DB manager ``prep_empty`` method no longer called (had been deprecated)
  - Python 2 support removed
  - Flask changed app's ``json_encoder/json_decoder`` attributes to ``_json_encoder/_json_decoder``
