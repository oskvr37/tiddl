import click

from .fav import FavGroup
from .file import FileGroup
from .search import SearchGroup
from .url import UrlGroup

from utils import Context, passContext

from tiddl.types import TrackArg


@click.command("download")
@click.option("--quality", default="normal", type=click.Choice(TrackArg.__args__))
@passContext
def DownloadCommand(ctx: Context, quality: str):
    """Download the tracks"""

    tracks = ctx.obj.tracks

    if not tracks:
        click.echo("No tracks found.")
        return

    for track in tracks:
        click.echo(f"Downloading {track['title']}")


UrlGroup.add_command(DownloadCommand)
SearchGroup.add_command(DownloadCommand)
FavGroup.add_command(DownloadCommand)
FileGroup.add_command(DownloadCommand)
