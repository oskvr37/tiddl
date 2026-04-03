from typer import Typer

from .url import url_subcommand
from .fav import fav_subcommand
from .search import search_subcommand


SUBCOMMANDS: list[Typer] = [url_subcommand, fav_subcommand, search_subcommand]


def register_subcommands(app: Typer):
    for sub_command in SUBCOMMANDS:
        app.add_typer(sub_command)
