import click

from .utils import ContextObj, passContext, Context
from .auth import AuthGroup
from .download_groups import UrlGroup, FavGroup, SearchGroup, FileGroup


@click.group()
@passContext
@click.option("--verbose", is_flag=True, help="Show debug logs")
def cli(ctx: Context, verbose: bool):
    """TIDDL - Download Tidal tracks ✨"""
    ctx.obj = ContextObj(verbose)


cli.add_command(AuthGroup)
cli.add_command(UrlGroup)
cli.add_command(FavGroup)
cli.add_command(SearchGroup)
cli.add_command(FileGroup)

if __name__ == "__main__":
    cli()
