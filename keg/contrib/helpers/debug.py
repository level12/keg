try:
    import sqlparse.format as sqlformat
except ImportError:
    def sqlformat(query, **kwargs):
        """Monkey patch sqlparse.format if package not installed"""
        return query


def debug_query(query, engine):
    """Return a parametrized and formated sql query for debugging

    See the docs http://goo.gl/eshjL2 for the details on how this works
    """

    q = unicode(query.compile(engine, compile_kwargs={'literal_binds': True}))
    return sqlformat(q, reindent=True)
