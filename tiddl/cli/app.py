import typer
import logging
from rich.console import Console
from typing_extensions import Annotated

from tiddl.cli.config import APP_PATH, CONFIG
from tiddl.cli.ctx import ContextObject, Context
from tiddl.cli.commands import register_commands

log = logging.getLogger("tiddl")

app = typer.Typer(name="tiddl", no_args_is_help=True, rich_markup_mode="rich")
register_commands(app)


@app.callback()
def callback(
    ctx: Context,
    OMIT_CACHE: Annotated[
        bool,
        typer.Option(
            "--omit-cache",
        ),
    ] = not CONFIG.enable_cache,
    DEBUG: Annotated[
        bool,
        typer.Option(
            "--debug",
        ),
    ] = CONFIG.debug,
):
    """
    tiddl - download tidal tracks \u266b

    [link=https://github.com/oskvr37/tiddl]github[/link]
    [link=https://buymeacoffee.com/oskvr][yellow]buy me a coffee[/link] \u2764
    """

    log.debug(f"{ctx.params=}")

    if DEBUG:
        debug_path = APP_PATH / "api_debug"
    else:
        debug_path = None

    ctx.obj = ContextObject(
        api_omit_cache=OMIT_CACHE, console=Console(), debug_path=debug_path
    )
