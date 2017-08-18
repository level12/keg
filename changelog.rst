Changelog
=========

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
