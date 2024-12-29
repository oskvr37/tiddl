import click

from .config import CONFIG_PATH, Config


@click.command("config")
@click.option(
    "--open",
    "-o",
    is_flag=True,
    help="Open the configuration file with the default editor",
)
def ConfigCommand(open: bool):
    """Print path to the configuration file"""

    click.echo(str(CONFIG_PATH))

    if open:
        click.launch(str(CONFIG_PATH))
