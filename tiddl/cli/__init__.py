import click
import logging

from rich.logging import RichHandler

from .ctx import ContextObj, passContext, Context
from .auth import AuthGroup
from .download import UrlGroup, FavGroup, SearchGroup, FileGroup
from .config import ConfigCommand

from tiddl.config import HOME_PATH

from .auth import refresh


@click.group()
@passContext
@click.option("--verbose", "-v", is_flag=True, help="Show debug logs.")
@click.option("--quiet", "-q", is_flag=True, help="Suppress logs.")
@click.option(
    "--no-cache", "-nc", is_flag=True, help="Omit Tidal API requests caching."
)
def cli(ctx: Context, verbose: bool, quiet: bool, no_cache: bool):
    """TIDDL - Tidal Downloader \u266b"""
    ctx.obj = ContextObj(omit_cache=no_cache)

    # latest logs
    file_handler = logging.FileHandler(
        HOME_PATH / "tiddl.log", mode="w", encoding="utf-8"
    )

    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(levelname)s [%(name)s.%(funcName)s] %(message)s", datefmt="[%X]"
        )
    )

    LEVEL = (
        logging.DEBUG if verbose else logging.ERROR if quiet else logging.INFO
    )

    rich_handler = RichHandler(console=ctx.obj.console, rich_tracebacks=True)
    rich_handler.setLevel(LEVEL)

    if LEVEL == logging.DEBUG:
        rich_handler.setFormatter(
            logging.Formatter(
                "[%(name)s.%(funcName)s] %(message)s", datefmt="[%X]"
            )
        )

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            rich_handler,
            file_handler,
        ],
        format="%(message)s",
        datefmt="[%X]",
    )

    logging.getLogger("urllib3").setLevel(logging.ERROR)

    # BUG: tiddl raises AuthError after token refresh,
    # probably ctx is not working like this.
    # NOTE: got 'fixed',
    # but i will know if it works after my token expire

    if ctx.invoked_subcommand in ("fav", "file", "search", "url"):
        ctx.invoke(refresh)


cli.add_command(ConfigCommand)
cli.add_command(AuthGroup)
cli.add_command(UrlGroup)
cli.add_command(FavGroup)
cli.add_command(SearchGroup)
cli.add_command(FileGroup)

if __name__ == "__main__":
    cli()
