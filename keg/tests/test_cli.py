from keg_apps.cli import CLIApp
from keg.testing import CLIBase


class TestCLI(CLIBase):
    app_cls = CLIApp
    cmd_name = 'hello'

    def test_class_command(self):
        result = self.invoke()
        assert 'hello keg test\n' == result.output

    def test_arg_command(self):
        result = self.invoke(cmd_name='foo2')
        assert 'hello foo\n' == result.output

    def test_argument_passing(self):
        result = self.invoke('bar', cmd_name='foo2')
        assert 'hello bar\n' == result.output

    def test_missing_command(self):
        result = self.invoke(cmd_name='baz', exit_code=2)
        assert 'No such command "baz"' in result.output


class TestConfigCommand(CLIBase):
    app_cls = CLIApp
    cmd_name = 'develop config'

    def test_output(self):
        result = self.invoke()
        # use a value that should be towards the end of the output as a reasonble indicator the
        # command worked as expected.
        assert 'USE_X_SENDFILE = False' in result.output
