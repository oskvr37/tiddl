import click

from .fav import FavGroup
from .file import FileGroup
from .search import SearchGroup
from .url import UrlGroup

from ..ctx import Context, passContext

from tiddl.download import downloadTrackStream
from tiddl.types import TrackArg, ARG_TO_QUALITY


@click.command("download")
@click.option("--quality", "-q", type=click.Choice(TrackArg.__args__))
@passContext
def DownloadCommand(ctx: Context, quality: TrackArg):
    """Download the tracks"""

    download_quality = ARG_TO_QUALITY[
        quality or ctx.obj.config.config["download"]["quality"]
    ]

    # TODO: fetch tracks from database
    # or from api

    tracks = []

    if not tracks:
        click.echo("No tracks found.")
        return

    api = ctx.obj.getApi()

    for track in tracks:
        click.echo(f"Downloading {track.title}")
        track_stream = api.getTrackStream(track.id, download_quality)
        stream_data, file_extension = downloadTrackStream(track_stream)

        with open(f"{track.id}.{file_extension}", "wb") as f:
            f.write(stream_data)


UrlGroup.add_command(DownloadCommand)
SearchGroup.add_command(DownloadCommand)
FavGroup.add_command(DownloadCommand)
FileGroup.add_command(DownloadCommand)
