import typer
from logging import getLogger
from rich.console import Console

# from typing_extensions import Annotated

from tiddl.cli.ctx import Context
from tiddl.cli.commands.subcommands import url_subcommand
from tiddl.cli.commands.auth import refresh

export_command = typer.Typer(name="export")
export_command.add_typer(url_subcommand)

log = getLogger(__name__)
console = Console()


@export_command.callback(no_args_is_help=True)
def export_callback(ctx: Context):
    """
    Export Tidal data.

    You can export the data to json file
    or pipe it to another process.
    """

    ctx.invoke(refresh)

    # TODO implement export functionality

    # exported structure
    # [{resource_type: str, resource_id: str|int, album: {...}, album_items: {...}}]

    # export to single files like id.json
    # or export all in one

    def handle_export():
        console.print(ctx.obj.resources)

    ctx.call_on_close(handle_export)
