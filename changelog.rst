Changelog
=========

0.8.0 released 2019-03-25
-------------------------

- BREAKING CHANGE: Remove web.BaseView awareness of xhr() method and remove dependency on the
  deprecated flask.request.is_xhr (0899c5d_)
- improve CI (3311389_)
- Update to support Flask 1.0+ (63e3667_)
- remove Pipenv including updated readme & tox (03b3920_)

.. _3311389: https://github.com/level12/keg/commit/3311389
.. _63e3667: https://github.com/level12/keg/commit/63e3667
.. _03b3920: https://github.com/level12/keg/commit/03b3920
.. _0899c5d: https://github.com/level12/keg/commit/0899c5d


0.7.0 released 2019-02-07
-------------------------

- Enable setting engine options from KEG variable (5bb807f_)

.. _5bb807f: https://github.com/level12/keg/commit/5bb807f


0.6.6 released 2018-11-13
-------------------------

- Add optional i18n support using morphi (d75a8fb_)
- Update pipenv dependencies to remove warning (b3b089e_)
- Pass through CLI invocation arguments and allow STDIN in CLI tests (bac2e3b_)

.. _d75a8fb: https://github.com/level12/keg/commit/d75a8fb
.. _b3b089e: https://github.com/level12/keg/commit/b3b089e
.. _bac2e3b: https://github.com/level12/keg/commit/bac2e3b


0.6.5 released 2018-05-28
-------------------------

- Update readme, start using pipenv, pin Flask < 1.0 (abdc9bf_)

.. _abdc9bf: https://github.com/level12/keg/commit/abdc9bf


0.6.4 released 2018-01-09
-------------------------

- when testing, don't log to syslog by default (304a0a7_)

.. _304a0a7: https://github.com/level12/keg/commit/304a0a7


0.6.3 released 2018-01-09
-------------------------

- add '@cee:' prefix to json syslog formatter (b7ea5d3_)

.. _b7ea5d3: https://github.com/level12/keg/commit/b7ea5d3


0.6.2 released 2017-12-19
-------------------------

- db: get rid of code to replace session object (149b42c_)

.. _149b42c: https://github.com/level12/keg/commit/149b42c


0.6.1 released 2017-11-16
-------------------------

- fix quiet logging (e46fd2b_)
- a few small updates/fixes to readme (2044439_)

.. _e46fd2b: https://github.com/level12/keg/commit/e46fd2b
.. _2044439: https://github.com/level12/keg/commit/2044439


0.6.0 released 2017-08-18
-------------------------

- ADD: make CLIBase operate off `current_app` as last resort (1b358c1_)
- ADD: --quiet option to script options (6eb723f_)
- BREAKING CHANGE: adjust cli API on KegApp (af45880_)

.. _1b358c1: https://github.com/level12/keg/commit/1b358c1
.. _6eb723f: https://github.com/level12/keg/commit/6eb723f
.. _af45880: https://github.com/level12/keg/commit/af45880


0.5.1 released 2017-08-15
-------------------------

- ADD: mitigate CSRF bug in Flask-WTF (42a2e70_)
- ADD: config, init, and routing enhancements (cdfa901_)
- MAINT: upgrade to CircleCI 2.0 (60e3bfa_)

.. _42a2e70: https://github.com/level12/keg/commit/42a2e70
.. _cdfa901: https://github.com/level12/keg/commit/cdfa901
.. _60e3bfa: https://github.com/level12/keg/commit/60e3bfa


0.5.0 released 2017-06-27
-------------------------

- prep for pyp usage (23424b9_)
- Merge branch 'logging-improvements' (PR66_)

.. _23424b9: https://github.com/level12/keg/commit/23424b9
.. _PR66: https://github.com/level12/keg/pull/66



0.4.1 - 2017-02-09
------------------

* BUG: Properly quote pgsql identifiers during create (86852ad_)

.. _86852ad: https://github.com/level12/keg/commit/86852ad



0.4.0 - 2016-12-19
------------------

* BUG: Properly Update Keyring Config Data (7f1908f_)
* MSSQL dialect support (df7e89d_)
* MAINT: Refactor keyring to accept bytes (15bc04b_)
* MAINT: Remove deprecated flask hooks (4f7e2bf_)
* Remove unicode_literal futures (dc2fa85_)
* MAINT: Create windows build environment (983e040_)
* MAINT: Run CI with Docker (bc7a877_)
* Remove extra cp in readme (7e94815_)

.. _7f1908f: https://github.com/level12/keg/commit/7f1908f
.. _df7e89d: https://github.com/level12/keg/commit/df7e89d
.. _15bc04b: https://github.com/level12/keg/commit/15bc04b
.. _4f7e2bf: https://github.com/level12/keg/commit/4f7e2bf
.. _dc2fa85: https://github.com/level12/keg/commit/dc2fa85
.. _983e040: https://github.com/level12/keg/commit/983e040
.. _bc7a877: https://github.com/level12/keg/commit/bc7a877
.. _7e94815: https://github.com/level12/keg/commit/7e94815
