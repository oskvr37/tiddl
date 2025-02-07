import click
import logging

from .ctx import ContextObj, passContext, Context
from .auth import AuthGroup
from .download import UrlGroup, FavGroup, SearchGroup, FileGroup
from .config import ConfigCommand

from tiddl.config import HOME_PATH


@click.group()
@passContext
@click.option("--verbose", "-v", is_flag=True, help="Show debug logs")
def cli(ctx: Context, verbose: bool):
    """TIDDL - Download Tidal tracks \u266b"""
    ctx.obj = ContextObj()

    # TODO: add rich console to ctx.obj, edit logging config,
    # add more verbosity options (silent, info, debug),
    # maybe logging format configuration

    # latest logs
    file_handler = logging.FileHandler(HOME_PATH / "tiddl.log", mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            stream_handler,
            file_handler,
        ],
        format="%(levelname)s [%(name)s.%(funcName)s] %(message)s",
    )

    logging.getLogger("urllib3").setLevel(logging.ERROR)


cli.add_command(ConfigCommand)
cli.add_command(AuthGroup)
cli.add_command(UrlGroup)
cli.add_command(FavGroup)
cli.add_command(SearchGroup)
cli.add_command(FileGroup)

if __name__ == "__main__":
    cli()
