import click

from tiddl.config import CONFIG_PATH

from .ctx import Context, passContext


@click.command("config")
@click.option(
    "--open",
    "-o",
    "OPEN_CONFIG",
    is_flag=True,
    help="Open the configuration file with the default editor.",
)
@click.option(
    "--locate",
    "-l",
    "LOCATE_CONFIG",
    is_flag=True,
    help="Launch a file manager with the located configuration file.",
)
@click.option(
    "--print",
    "-p",
    "PRINT_CONFIG",
    is_flag=True,
    help="Show current configuration.",
)
@passContext
def ConfigCommand(
    ctx: Context, OPEN_CONFIG: bool, LOCATE_CONFIG: bool, PRINT_CONFIG: bool
):
    """
    Configuration file options.

    By default it prints location of tiddl config file.

    This command can be used in variable like `vim $(tiddl config)`
    - this will open your config with vim editor.
    """

    if OPEN_CONFIG:
        click.launch(str(CONFIG_PATH))

    elif LOCATE_CONFIG:
        click.launch(str(CONFIG_PATH), locate=True)

    elif PRINT_CONFIG:
        config_without_auth = ctx.obj.config.model_copy()
        del config_without_auth.auth
        ctx.obj.console.print(config_without_auth.model_dump_json(indent=2))

    else:
        click.echo(str(CONFIG_PATH))
