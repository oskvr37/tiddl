import click

from pathlib import Path

from .fav import FavGroup
from .file import FileGroup
from .search import SearchGroup
from .url import UrlGroup

from ..ctx import Context, passContext

from tiddl.download import downloadTrackStream
from tiddl.models import TrackArg, ARG_TO_QUALITY, Track
from tiddl.utils import TidalResource, formatTrack
from tiddl.api import TidalApi


class TrackCollector:
    def __init__(self, api: TidalApi):
        self.api = api
        self.tracks: list[Track] = []

    def addResource(self, resource: TidalResource):
        try:
            match resource.type:
                case "track":
                    track = self.api.getTrack(resource.id)
                    self._addTrack(track)

                case "album":
                    album_tracks = self.api.getAlbumItems(resource.id)
                    self._addItems(album_tracks.items)

                case "playlist":
                    playlist_tracks = self.api.getPlaylistItems(resource.id)
                    self._addItems(playlist_tracks.items)

                case "artist":
                    artist_albums = self.api.getArtistAlbums(resource.id)
                    for artist_album in artist_albums.items:
                        album_tracks = self.api.getAlbumItems(artist_album.id)
                        self._addItems(album_tracks.items)

        except Exception as e:
            click.echo(click.style(f"Error in adding resource: {resource}, {e}", "red"))

    def _addTrack(self, track: Track):
        if track.allowStreaming:
            self.tracks.append(track)

    def _addItems(self, items):
        for item in items:
            if item.type == "track":
                self._addTrack(item.item)


@click.command("download")
@click.option("--quality", "-q", type=click.Choice(TrackArg.__args__))
@click.option("--output", "-o", type=str)
@passContext
def DownloadCommand(ctx: Context, quality: TrackArg, output: str):
    """Download the tracks"""

    api = ctx.obj.getApi()
    track_collector = TrackCollector(api)

    for resource in ctx.obj.resources:
        track_collector.addResource(resource)

    if not track_collector.tracks:
        click.echo("No tracks found.")
        return

    download_quality = ARG_TO_QUALITY[quality or ctx.obj.config.download.quality]
    template = output or ctx.obj.config.download.template

    for track in track_collector.tracks:
        click.echo(f"Downloading {track.title}")
        track_stream = api.getTrackStream(track.id, download_quality)
        stream_data, file_extension = downloadTrackStream(track_stream)

        file_name = formatTrack(template, track)
        path = Path(f"{file_name}.{file_extension}")
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("wb") as f:
            f.write(stream_data)


UrlGroup.add_command(DownloadCommand)
SearchGroup.add_command(DownloadCommand)
FavGroup.add_command(DownloadCommand)
FileGroup.add_command(DownloadCommand)
