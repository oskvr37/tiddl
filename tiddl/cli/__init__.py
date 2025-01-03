import click
import logging

from .ctx import ContextObj, passContext, Context
from .auth import AuthGroup
from .download import UrlGroup, FavGroup, SearchGroup, FileGroup
from .config import ConfigCommand


@click.group()
@passContext
@click.option("--verbose", "-v", is_flag=True, help="Show debug logs")
def cli(ctx: Context, verbose: bool):
    """TIDDL - Download Tidal tracks ✨"""
    ctx.obj = ContextObj()

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        handlers=[logging.StreamHandler()],
        format="%(levelname)s [%(name)s.%(funcName)s] %(message)s",
    )


cli.add_command(ConfigCommand)
cli.add_command(AuthGroup)
cli.add_command(UrlGroup)
cli.add_command(FavGroup)
cli.add_command(SearchGroup)
cli.add_command(FileGroup)

if __name__ == "__main__":
    cli()
