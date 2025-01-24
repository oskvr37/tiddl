import click

from .fav import FavGroup
from .file import FileGroup
from .search import SearchGroup
from .url import UrlGroup

from ..ctx import Context, passContext

from tiddl.download import downloadTrackStream
from tiddl.models import TrackArg, ARG_TO_QUALITY, Track, PlaylistTrack
from tiddl.utils import formatTrack


@click.command("download")
@click.option("--quality", "-q", type=click.Choice(TrackArg.__args__))
@click.option(
    "--output", "-o", "template", type=str, help="Format track file template."
)
@passContext
def DownloadCommand(ctx: Context, quality: TrackArg | None, template: str | None):
    """Download the tracks"""

    download_quality = ARG_TO_QUALITY[quality or ctx.obj.config.download.quality]
    download_path = ctx.obj.config.download.path

    api = ctx.obj.getApi()

    def downloadTrack(track: Track, file_name: str) -> None:
        if not track.allowStreaming:
            click.echo(
                f"{click.style('✖', 'yellow')} Track {click.style(file_name, 'yellow')} does not allow streaming"
            )
            return

        click.echo(
            f"{click.style('✔', 'green')} Downloading track {click.style(file_name, 'green')}"
        )

        # TODO: check if file already exists.
        # will need to predict file extension

        track_stream = api.getTrackStream(track.id, download_quality)
        stream_data, file_extension = downloadTrackStream(track_stream)

        path = download_path / f"{file_name}.{file_extension}"
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("wb") as f:
            f.write(stream_data)

    # TODO: check for artists in resources
    # then add their resources to the list

    for resource in ctx.obj.resources:
        match resource.type:
            case "track":
                track = api.getTrack(resource.id)
                file_name = formatTrack(
                    template=template or ctx.obj.config.template.track, track=track
                )

                downloadTrack(
                    track=track,
                    file_name=file_name,
                )

            case "album":
                album = api.getAlbum(resource.id)
                click.echo(f"★ Album {album.title}")

                # TODO: fetch all items
                album_items = api.getAlbumItems(resource.id, limit=100)

                for item in album_items.items:
                    if isinstance(item.item, Track):
                        track = item.item

                        file_name = formatTrack(
                            template=template or ctx.obj.config.template.album,
                            track=track,
                            album_artist=album.artist.name,
                        )

                        downloadTrack(track=track, file_name=file_name)

            case "playlist":
                playlist = api.getPlaylist(resource.id)
                click.echo(f"★ Playlist {playlist.title}")

                # TODO: fetch all items
                playlist_items = api.getPlaylistItems(resource.id)

                for item in playlist_items.items:
                    if isinstance(item.item, PlaylistTrack):
                        track = item.item

                        file_name = formatTrack(
                            template=template or ctx.obj.config.template.playlist,
                            track=track,
                            playlist_title=playlist.title,
                            playlist_index=track.index // 100000,
                        )

                        downloadTrack(track=item.item, file_name=file_name)


UrlGroup.add_command(DownloadCommand)
SearchGroup.add_command(DownloadCommand)
FavGroup.add_command(DownloadCommand)
FileGroup.add_command(DownloadCommand)
