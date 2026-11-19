Internationalization
====================

Keg can optionally be installed with the ``morphi`` library to use ``babel`` for internationalization::

    pip install keg[i18n]

The Babel command settings live in ``pyproject.toml``. For ease of development
and ensuring that all marked strings have translations, a Nox session updates
and compiles the catalogs and reports any strings that need to be added.

Run the session, update strings in the PO files as necessary, rerun it until it
passes, and then commit the catalog changes.

.. code::

    uv run nox -s i18n
