Installation
============

``pip install keg``


Upgrade Notes
=============

While we attempt to preserve backward compatibility, some Keg versions do introduce
breaking changes. This list should provide information on needed app changes.

- 0.11.0

  - App context is no longer pushed as part of test suite setup

    - Having the app context pushed there was problematic because extensions can rely on
      ``flask.g`` refreshing for each request
    - Generally, when processing requests, flask will push a fresh app context. However, this
      does not occur if a context is already present.
    - While that concern is resolved most directly in flask-webtest 0.1.1 by directly pushing
      an app context as part of the request process, keg needs to stop tying the test framework
      and the context so closely together. An app's test suite needs to be able to set up and
      tear down contexts as needed.
    - pytest does not yet support passing fixtures to setup methods. Thus, for the time being,
      to have database use available in setup methods (since flask-sqlalchemy ties that session
      to an app context), auto-used fixtures will be needed. Ensure the scope of the auto-used
      fixture matches the level of setup methods needed in the suite (module, class, etc.)
    - Mocking can be affected in the test suite as well. Any mocks requiring app context will
      need to happen at run time, rather than import time

      - E.g. ``@mock.patch.dict(flask.current_app.config, ...)`` becomes
        ``@mock.patch.dict('flask.current_app.config', ...)``

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
