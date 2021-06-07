from __future__ import absolute_import

from collections import defaultdict
from contextlib import contextmanager

import click
import flask
import flask.cli
from six.moves import urllib

from keg import current_app
from keg.extensions import gettext as _


try:
    import dotenv
except ImportError:
    dotenv = None

try:
    from flask.helpers import get_load_dotenv
except ImportError:
    def get_load_dotenv(default=False):
        return False


class KegAppGroup(flask.cli.AppGroup):
    def __init__(self, create_app, add_default_commands=True, load_dotenv=True, *args, **kwargs):
        self.create_app = create_app
        self.load_dotenv = load_dotenv

        flask.cli.AppGroup.__init__(self, *args, **kwargs)
        if add_default_commands:
            self.add_command(dev_command)

        self._loaded_plugin_commands = False

    def _load_plugin_commands(self):
        if self._loaded_plugin_commands:
            return
        try:
            import pkg_resources
        except ImportError:
            self._loaded_plugin_commands = True
            return

        for ep in pkg_resources.iter_entry_points('flask.commands'):
            self.add_command(ep.load(), ep.name)
        for ep in pkg_resources.iter_entry_points('keg.commands'):
            self.add_command(ep.load(), ep.name)
        self._loaded_plugin_commands = True

    def list_commands(self, ctx):
        self._load_plugin_commands()

        info = ctx.ensure_object(flask.cli.ScriptInfo)
        info.load_app()
        rv = set(click.Group.list_commands(self, ctx))
        return sorted(rv)

    def get_command(self, ctx, name):
        info = ctx.ensure_object(flask.cli.ScriptInfo)
        info.load_app()
        return click.Group.get_command(self, ctx, name)

    def main(self, *args, **kwargs):
        if get_load_dotenv(self.load_dotenv):
            flask.cli.load_dotenv()

        obj = kwargs.get('obj')
        if obj is None:
            obj = flask.cli.ScriptInfo(create_app=self.create_app)
        kwargs['obj'] = obj
        # TODO: figure out if we want to use this next line.
        #kwargs.setdefault('auto_envvar_prefix', 'FLASK')
        return flask.cli.AppGroup.main(self, *args, **kwargs)


@click.group('develop', help=_('Developer info and utils.'))
def dev_command():
    pass


dev_command.add_command(flask.cli.run_command)
dev_command.add_command(flask.cli.shell_command)


@dev_command.command('routes', short_help=_('List the routes defined for this app.'))
@flask.cli.with_appcontext
def routes_command():
    output = []
    endpoint_len = 0
    methods_len = 0

    # calculate how wide the output columns need to be
    for rule in flask.current_app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        endpoint_len = max(endpoint_len, len(rule.endpoint))
        methods_len = max(methods_len, len(methods))

    # generate the output
    for rule in flask.current_app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.parse.unquote("{}   {}   {}".format(
            rule.endpoint.ljust(endpoint_len), methods.ljust(methods_len), rule))
        output.append(line)

    for line in sorted(output):
        click.echo(line)


@dev_command.command('templates', short_help=_('Show paths searched for a template.'))
@flask.cli.with_appcontext
def templates_command():
    jinja_loader = flask.current_app.jinja_env.loader
    paths = defaultdict(list)
    for template in jinja_loader.list_templates():
        for loader, template in jinja_loader._iter_loaders(template):
            for dpath in loader.searchpath:
                paths[dpath].append(template)
    for dpath in sorted(paths.keys()):
        template_paths = sorted(paths[dpath])
        click.echo(dpath)
        for tpath in template_paths:
            click.echo('    {}'.format(tpath))


@dev_command.command('config', short_help=_('List info related to config files, profiles, and'
                     ' values.'))
@flask.cli.with_appcontext
def config_command():
    app = flask.current_app
    config = app.config
    keys = list(config.keys())
    keys.sort()

    click.echo(_('Default config objects:'))
    for val in config.default_config_locations_parsed():
        click.echo('    {}'.format(val))

    click.echo(_('Config file locations:'))
    for val in config.config_file_paths():
        click.echo('    {}'.format(val))

    if config.config_paths_unreadable:
        click.echo(_('Could not access the following config paths:'))
        for path, exc in config.config_paths_unreadable:
            click.echo('    {}: {}'.format(path, str(exc)))

    click.echo(_('Config objects used:'))
    for val in config.configs_found:
        click.echo('    {}'.format(val))

    click.echo(_('Resulting app config (including Flask defaults):'))
    for key in keys:
        click.echo('    {} = {}'.format(key, config[key]))


class DatabaseGroup(click.MultiCommand):

    def list_commands(self, ctx):
        return ['clear', 'init']

    def get_command(self, ctx, name):
        if name == 'init':
            return database_init
        if name == 'clear':
            return database_clear


@dev_command.command('db', cls=DatabaseGroup, invoke_without_command=True,
                     help=_('Lists database related sub-commands.'))
@flask.cli.with_appcontext
@click.pass_context
def database_group(ctx):
    # only take action if no subcommand is involved.
    if ctx.invoked_subcommand is None:
        if not current_app.db_enabled:
            click.echo(_('Database not enabled for this app.  No subcommands available.'))
        else:
            # Database enabled, but no subcommand was given, therefore we want to just show
            # the help message, which would be the default behavior if we had not used the
            # invoke_Without_command option.
            click.echo(ctx.get_help())
            ctx.exit()


@click.command('init', short_help=_('Create all db objects, send related events.'))
@click.option('--clear-first', default=False, is_flag=True,
              help=_('Clear DB of all data and drop all objects before init.'))
@flask.cli.with_appcontext
def database_init(clear_first):
    if clear_first:
        current_app.db_manager.db_init_with_clear()
        click.echo(_('Database cleared and initialized'))
    else:
        current_app.db_manager.db_init()
        click.echo(_('Database initialized'))


@click.command('clear', short_help=_('Clear DB of all data and drop all objects.'))
@flask.cli.with_appcontext
def database_clear():
    current_app.db_manager.db_clear()
    click.echo(_('Database cleared'))


class CLILoader(object):
    """
        This loader takes care of the complexity of click object setup and instantiation in the
        correct order so that application level CLI options are available before the Keg app is
        instantiated (so the options can be used to configure the app).

        The order of events is:

        - instantiate KegAppGroup
        - KegAppGroup.main() is called
            1. the ScriptInfo object is instantiated
            2. normal click behavior starts, including argument parsing
                - arguments are always parsed due to invoke_without_command=True
            3. during argument parsing, option callbacks are excuted which will result in at least
               the profile name being saved in ScriptInfo().data
            4. Normal click .main() behavior will continue which could include processing commands
               decorated with flask.cli.with_appcontext() or calls to KegAppGroup.list_commands()
               or KegAppGroup.get_command().
                - ScriptInfo.init_app() will be called during any of these operations
                - ScriptInfo.init_app() will call self.create_app() below with the ScriptInfo
                  instance
    """
    def __init__(self, appcls):
        self.appcls = appcls
        # Don't store instance-level vars here.  This object is only instantiated once per Keg
        # sub-class but can be used across multiple app instance creations.  So, anything app
        # instance specific should go on the ScriptInfo instance (see self.options_callback()).

    def create_group(self):
        """ Create the top most click Group instance which is the entry point for any Keg app
            being called in a CLI context.

            The return value of this context gets set on Keg.cli
        """

        return KegAppGroup(
            self.create_app,
            params=self.create_script_options(),
            callback=self.main_callback,
            invoke_without_command=True,
        )

    def create_app(self, script_info=False):
        """ Instantiate our app, sending CLI option values through as needed.

            `script_info:` required for Flask 1.X create_app signature, but not valid in Flask 2.1.
            So keep it as an arg, but don't use it to get the object.  See #163.
        """
        script_info = click.get_current_context().obj
        init_kwargs = self.option_processor(script_info.data)
        return self.appcls().init(**init_kwargs)

    def option_processor(self, cli_options):
        """
            Turn cli_options, which is the result of all parsed options in create_script_options()
            into a dict which will be given as kwargs to the app's .init() method.
        """
        retval = dict(config_profile=cli_options.get('profile', None), config={})
        if cli_options.get('quiet', False):
            retval['config']['KEG_LOG_STREAM_ENABLED'] = False
        return retval

    def create_script_options(self):
        """ Create app level options, ideally that are used to configure the app itself.  """
        return [
            click.Option(['--profile'], is_eager=True, default=None, callback=self.options_callback,
                         help=_('Name of the configuration profile to use.'),),
            click.Option(['--quiet'], is_eager=True, is_flag=True, default=False,
                         callback=self.options_callback,
                         help=_('Set default logging level to logging.WARNING.')),
            click.Option(['--help-all'], is_eager=True, is_flag=True, expose_value=False,
                         callback=self.help_all_callback,
                         help=_('Show all commands with subcommands.')),
        ]

    def options_callback(self, ctx, param, value):
        """ This method is called after argument parsing, after ScriptInfo instantiation but before
            create_app() is called.  It's the only way to get the options into ScriptInfo.data
            before the Keg app instance is instantiated.
        """
        si = ctx.ensure_object(flask.cli.ScriptInfo)
        si.data[param.name] = value

    def help_all_callback(self, ctx, param, value):
        if not value or ctx.resilient_parsing:
            return
        formatter = ctx.make_formatter()

        ctx.command.format_usage(ctx, formatter)
        ctx.command.format_help_text(ctx, formatter)
        self.format_options(ctx.command, ctx, formatter)
        self.format_commands(ctx.command, ctx, formatter)
        ctx.command.format_epilog(ctx, formatter)

        click.echo(formatter.getvalue().rstrip('\n'))
        ctx.exit()

    def format_options(self, command, ctx, formatter):
        opts = []
        for param in command.get_params(ctx):
            if param.name == 'help':
                opts.append(('--help', _('Show help message.')))
            elif param.name == 'help_all':
                opts.append(('--help-all', _('Show this message and exit.')))
            else:
                rv = param.get_help_record(ctx)
                if rv is not None:
                    opts.append(rv)

        if opts:
            with formatter.section('Options'):
                formatter.write_dl(opts)

    def format_commands(self, command, ctx, formatter):
        if hasattr(command, 'list_commands'):
            subcommands = command.list_commands(ctx)

            if len(subcommands):
                # allow for 3 times the default spacing
                limit = formatter.width - 6 - max(len(subcommand) for subcommand in subcommands)

                rows = []
                commands = []
                for subcommand in subcommands:
                    cmd = command.get_command(ctx, subcommand)
                    if cmd is None:
                        continue
                    if cmd.hidden:
                        continue
                    commands.append(cmd)
                    help = cmd.get_short_help_str(limit)
                    rows.append((subcommand, help))

                with self.compact_section(formatter, 'Commands'):
                    self.write_dl_with_subcommands(ctx, formatter, rows, commands)

    def write_dl_with_subcommands(self, ctx, formatter, rows, commands, col_max=30, col_spacing=2):
        rows = list(rows)
        widths = click.formatting.measure_table(rows)
        if len(widths) != 2:
            raise TypeError('Expected two columns for definition list')

        first_col = min(widths[0], col_max) + col_spacing

        for (first, second), command in zip(
            click.formatting.iter_rows(rows, len(widths)), commands
        ):
            formatter.write('%*s%s' % (formatter.current_indent, '', first))
            if not second:
                formatter.write('\n')
                continue
            if click.formatting.term_len(first) <= first_col - col_spacing:
                formatter.write(' ' * (first_col - click.formatting.term_len(first)))
            else:
                formatter.write('\n')
                formatter.write(' ' * (first_col + formatter.current_indent))

            text_width = max(formatter.width - first_col - 2, 10)
            lines = iter(click.formatting.wrap_text(second, text_width).splitlines())
            if lines:
                formatter.write(next(lines) + '\n')
                for i, line in enumerate(lines):
                    formatter.write('%*s%s\n' % (
                        first_col + formatter.current_indent, '', line))
            else:
                formatter.write('\n')

            # Add subcommands under current command (recursive)
            with formatter.indentation():
                self.format_commands(command, ctx, formatter)

    @contextmanager
    def compact_section(self, formatter, name):
        formatter.write_heading(name)
        formatter.indent()
        try:
            yield
        finally:
            formatter.dedent()

    def main_callback(self, **kwargs):
        """
            Default Click behavior is to call the help method if no arguments are given to the
            top-most command.  That's good UX, but the way Click impliments it, the help is
            shown before argument parsing takes place.  That's bad, because it means our
            options_callback() is never called and the config profile isn't available when the
            help command calls KegAppGroup.list_commands().

            So, we force Click to always parse the args using `invoke_without_command=True` above,
            but when we do that, Click turns off the automatic display of help.  So, we just
            impliment help-like behavior in this method, which gives us the same net result
            as default Click behavior.
        """
        ctx = click.get_current_context()

        if ctx.invoked_subcommand is not None:
            # A subcommand is present, so arguments were passed.
            return

        click.echo(ctx.get_help(), color=ctx.color)
        ctx.exit()
