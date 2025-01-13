import click

from .fav import FavGroup
from .file import FileGroup
from .search import SearchGroup
from .url import UrlGroup

from ..ctx import Context, passContext

from tiddl.download import downloadTrackStream
from tiddl.types import TrackArg, ARG_TO_QUALITY, Track


@click.command("download")
@click.option("--quality", "-q", type=click.Choice(TrackArg.__args__))
@passContext
def DownloadCommand(ctx: Context, quality: TrackArg):
    """Download the tracks"""

    download_quality = ARG_TO_QUALITY[
        quality or ctx.obj.config.config["download"]["quality"]
    ]

    api = ctx.obj.getApi()
    tracks: list[Track] = []

    def addTrack(track: Track):
        if track.allowStreaming:
            tracks.append(track)

    for resource in ctx.obj.resources:
        match resource.resource_type:
            case "track":
                try:
                    track = api.getTrack(resource.resource_id)
                    addTrack(track)
                except Exception as e:
                    print(e)

            case "album":
                album_tracks = api.getAlbumItems(resource.resource_id)
                for album_item in album_tracks.items:
                    if album_item.type == "track":
                        addTrack(album_item.item)

    if not tracks:
        click.echo("No tracks found.")
        return

    for track in tracks:
        click.echo(f"Downloading {track.title}")
        track_stream = api.getTrackStream(track.id, download_quality)
        stream_data, file_extension = downloadTrackStream(track_stream)

        with open(
            f"{track.id}.{track_stream.audioQuality.lower()}.{file_extension}",
            "wb",
        ) as f:
            f.write(stream_data)


UrlGroup.add_command(DownloadCommand)
SearchGroup.add_command(DownloadCommand)
FavGroup.add_command(DownloadCommand)
FileGroup.add_command(DownloadCommand)
