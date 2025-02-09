import click

from tiddl.config import CONFIG_PATH


@click.command("config")
@click.option(
    "--open",
    "-o",
    is_flag=True,
    help="Open the configuration file with the default editor.",
)
@click.option(
    "--locate",
    "-l",
    is_flag=True,
    help="Launch a file manager with the located configuration file.",
)
def ConfigCommand(open: bool, locate: bool):
    """
    Configuration file options.

    By default it prints location of tiddl config file.

    This command can be used in variable like `vim $(tiddl config)`
    - this will open your config with vim editor.
    """

    if open:
        click.launch(str(CONFIG_PATH))
    elif locate:
        click.launch(str(CONFIG_PATH), locate=True)
    else:
        click.echo(str(CONFIG_PATH))
