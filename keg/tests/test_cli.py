import os
from unittest import mock

import pytest

from keg.cli import dotenv, get_load_dotenv
from keg.testing import CLIBase, app_config
from keg_apps.cli import CLIApp
from keg_apps.cli2.app import CLI2App
from keg_apps.db.app import DBApp


need_dotenv = pytest.mark.skipif(
    not get_load_dotenv() or dotenv is None, reason='dotenv not supported'
)


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
        assert 'No such command \'baz\'' in result.output

    @need_dotenv
    def test_dotenv(self):
        test_dir = os.path.dirname(__file__)
        # ensure flask looks in the expected working directory
        working_dir = os.path.abspath(os.path.join(test_dir, '..', '..'))
        os.chdir(working_dir)

        # Place dotenv file in search path of python-dotenv
        flaskenv = os.path.join(working_dir, '.flaskenv')
        try:
            with open(flaskenv, 'w') as f:
                f.write('FOO=bar')
            assert 'FOO' not in os.environ
            self.invoke()
            assert os.environ['FOO'] == 'bar'
        finally:
            os.remove(flaskenv)
            del os.environ['FOO']

    @need_dotenv
    @mock.patch.dict(os.environ, {'FLASK_SKIP_DOTENV': '1'})
    def test_disable_dotenv_from_env(self):
        test_dir = os.path.dirname(__file__)
        # ensure flask looks in the expected working directory
        working_dir = os.path.abspath(os.path.join(test_dir, '..', '..'))
        os.chdir(working_dir)

        # Place dotenv file in search path of python-dotenv
        flaskenv = os.path.join(working_dir, '.flaskenv')
        try:
            with open(flaskenv, 'w') as f:
                f.write('FOO=bar')
            assert 'FOO' not in os.environ
            self.invoke()
            assert 'FOO' not in os.environ
        finally:
            os.remove(flaskenv)

    @pytest.mark.skipif(True, reason='reminder')
    def test_default_exception_handling(self):
        """
            invoke_command() does some stuff to help with exceptions, it should be tested or
            removed.  So comment in that function for details.
        """


class TestCLI2(CLIBase):
    # We don't set an app_cls (see below), but we do want any current app context cleaned
    # up before constructing a new one.
    force_app_context_cleanup = True

    @classmethod
    def setup_class(cls):
        CLIBase.setup_class()
        # Use this, instead of setting app_cls on the testing class, in order to test that the
        # machinery in place for using the current app is working.
        CLI2App.testing_prep()

    def test_invoke(self):
        result = self.invoke('hello1')
        assert 'hello1' in result.output

    def test_no_commands_help_message(self):
        result = self.invoke()
        assert 'Usage: ' in result.output
        assert '--quiet         Set default logging level to logging.WARNING' in result.output
        assert '--profile TEXT  Name of the configuration profile to use.' in result.output
        assert '--help-all      Show all commands with subcommands.' in result.output
        assert 'develop       Developer info and utils.' in result.output
        assert 'hello1' in result.output

    def test_quiet(self):
        # the asserts for these tests are in keg_apps.cli2.cli
        result = self.invoke('--quiet', 'is-quiet')
        assert 'printed foo' in result.output
        assert 'logged foo' not in result.output

        result = self.invoke('is-not-quiet')
        assert 'printed foo' in result.output
        assert 'logged foo' in result.output

    def test_help_all(self):
        expected_lines = [
            'Usage', '', 'Options', '--profile', '--quiet', '--help-all', '--help',
            'Commands', 'develop', 'Commands', 'config', 'db', 'Commands', 'clear',
            'init', 'routes',
            'run', 'shell', 'templates', 'hello1', 'is-not-quiet', 'is-quiet', 'reverse',
            ''
        ]
        result = self.invoke('--help-all')
        output_lines = result.output.split('\n')
        assert len(expected_lines) == len(output_lines), result.output
        for command, line in zip(expected_lines, output_lines):
            assert line.lstrip().startswith(command), f'"{line}" does not start with "{command}"'

    def test_handle_input(self):
        result = self.invoke('reverse', input='abcde')
        assert 'Input: abcde' in result.output
        assert 'edcba' in result.output


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

    def test_app_config(self):
        with app_config(FOO_NAME='Bar'):
            result = self.invoke()
        assert 'Bar' in result.output


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
        assert 'Database initialized' in result.output
        m_db_init.assert_called_once_with()

    @mock.patch('keg.db.DatabaseManager.db_init_with_clear')
    def test_init_with_clear(self, m_db_init_wc):
        result = self.invoke('init', '--clear-first', '--yes')
        assert 'Database cleared and initialized' in result.output
        m_db_init_wc.assert_called_once_with()

    @mock.patch('keg.db.DatabaseManager.db_clear')
    def test_clear(self, m_db_clear):
        result = self.invoke('clear', '--yes')
        assert 'Database cleared' in result.output
        m_db_clear.assert_called_once_with()
