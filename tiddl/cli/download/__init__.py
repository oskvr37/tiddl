import click

from .fav import FavGroup
from .file import FileGroup
from .search import SearchGroup
from .url import UrlGroup

from ..ctx import Context, passContext

from tiddl.types import TrackArg, Track

DEFAULT_QUALITY: TrackArg = "normal"


def downloadTrack(track: Track, quality: TrackArg):
    # TODO: create download function
    # it should download track to user specified directory with specified filename
    # then add the track id to the database with file path and quality
    pass


@click.command("download")
@click.option(
    "--quality", default=DEFAULT_QUALITY, type=click.Choice(TrackArg.__args__)
)
@passContext
def DownloadCommand(ctx: Context, quality: TrackArg):
    """Download the tracks"""

    tracks = ctx.obj.tracks

    if not tracks:
        click.echo("No tracks found.")
        return

    for track in tracks:
        click.echo(f"Downloading {track['title']}")
        downloadTrack(track, quality)


UrlGroup.add_command(DownloadCommand)
SearchGroup.add_command(DownloadCommand)
FavGroup.add_command(DownloadCommand)
FileGroup.add_command(DownloadCommand)
