from __future__ import absolute_import
from __future__ import unicode_literals

import click
import click.testing


class CLIBase(object):
    # child classes will need to set these values in order to use the class
    app_cls = None
    cmd_name = None

    @classmethod
    def setup_class(cls):
        cls.runner = click.testing.CliRunner()

    def invoke(self, *args, **kwargs):
        exit_code = kwargs.pop('exit_code', 0)
        result = self.runner.invoke(
            self.app_cls.cli_group,
            [self.cmd_name] + list(args),
            catch_exceptions=False
        )
        assert result.exit_code == exit_code, result.output
        return result
