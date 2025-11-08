from typer import Typer

from .auth import auth_command
from .download import download_command
# from .export import export_command

COMMANDS = [
    auth_command,
    download_command,
    # export_command
]


def register_commands(app: Typer):
    for command in COMMANDS:
        app.add_typer(command, name=command.info.name)
