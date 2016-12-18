from __future__ import absolute_import

import tempfile

from keg.utils import pymodule_fpaths_to_objects


class TestUtils(object):

    def test_pymodule_fpaths_to_objects(self):
        with tempfile.NamedTemporaryFile(delete=False) as fh:
            fpath1 = fh.name
            fh.write(b'foo1="bar"')

        with tempfile.NamedTemporaryFile(delete=False) as fh:
            fpath2 = fh.name
            fh.write(b'foo2="bar"')

        with tempfile.NamedTemporaryFile() as fh:
            fpath3 = fh.name

        result = pymodule_fpaths_to_objects([fpath1, fpath2, fpath3])

        fpath, fpath_objs = result.pop(0)
        assert fpath == fpath1
        assert fpath_objs['foo1'] == 'bar'

        fpath, fpath_objs = result.pop(0)
        assert fpath == fpath2
        assert fpath_objs['foo2'] == 'bar'

        # result should now be empty since fpath3 should get filtered out b/c it's not present
        assert len(result) == 0
