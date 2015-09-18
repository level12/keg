from __future__ import absolute_import

import mock
import pytest

from keg_apps.cli import CLIApp
from keg_apps.db.app import DBApp
from keg.testing import CLIBase


class TestCLI(CLIBase):
    app_cls = CLIApp
    cmd_name = 'hello'

    def test_class_command(self):
        result = self.invoke()
        assert 'hello keg test' in result.output

    def test_arg_command(self):
        result = self.invoke(cmd_name='foo2')
        assert 'hello foo' in result.output

    def test_argument_passing(self):
        result = self.invoke('bar', cmd_name='foo2')
        assert 'hello bar' in result.output

    def test_missing_command(self):
        result = self.invoke(cmd_name='baz', exit_code=2)
        assert 'No such command "baz"' in result.output

    @pytest.mark.skipif(True, reason='reminder')
    def test_default_exception_handling(self):
        """
            invoke_command() does some stuff to help with exceptions, it should be tested or
            removed.  So comment in that function for details.
        """


class TestConfigCommand(CLIBase):
    app_cls = CLIApp
    cmd_name = 'develop config'

    def test_output(self):
        result = self.invoke()
        # use a value that should be towards the end of the output as a reasonble indicator the
        # command worked as expected.
        assert 'USE_X_SENDFILE = False' in result.output

    def test_database_disabled(self):
        result = self.invoke(cmd_name='develop db')
        assert 'Database not enabled for this app.  No subcommands available.' in result.output
        assert 'Lists database related sub-commands.' not in result.output


class TestDatabaseCommands(CLIBase):
    app_cls = DBApp
    cmd_name = 'develop db'

    def test_help_info(self):
        result = self.invoke()
        assert 'Lists database related sub-commands.' in result.output
        assert 'init   Create all db objects, send related events.' in result.output

    @mock.patch('keg.db.DatabaseManager.db_init')
    def test_init(self, m_db_init):
        result = self.invoke('init')
        assert 'Database initialzed' in result.output
        m_db_init.assert_called_once_with()

    @mock.patch('keg.db.DatabaseManager.db_init_with_clear')
    def test_init_with_clear(self, m_db_init_wc):
        result = self.invoke('init', '--clear-first')
        assert 'Database cleared and initialized' in result.output
        m_db_init_wc.assert_called_once_with()

    @mock.patch('keg.db.DatabaseManager.db_clear')
    def test_clear(self, m_db_clear):
        result = self.invoke('clear')
        assert 'Database cleared' in result.output
        m_db_clear.assert_called_once_with()
