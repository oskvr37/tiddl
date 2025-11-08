from typer import Typer

from .url import url_subcommand


SUBCOMMANDS: list[Typer] = [url_subcommand]


def register_subcommands(app: Typer):
    for sub_command in SUBCOMMANDS:
        app.add_typer(sub_command)
