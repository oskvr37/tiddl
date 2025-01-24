import click

from .fav import FavGroup
from .file import FileGroup
from .search import SearchGroup
from .url import UrlGroup

from ..ctx import Context, passContext

from tiddl.download import downloadTrackStream
from tiddl.models import TrackArg, ARG_TO_QUALITY, Track, PlaylistTrack, Album
from tiddl.utils import formatTrack, trackExists, TidalResource
from tiddl.metadata import addMetadata, Cover
from tiddl.exceptions import ApiError, AuthError


@click.command("download")
@click.option("--quality", "-q", "quality", type=click.Choice(TrackArg.__args__))
@click.option(
    "--output", "-o", "template", type=str, help="Format track file template."
)
@click.option(
    "--noskip",
    "-ns",
    "noskip",
    is_flag=True,
    default=False,
    help="Dont skip downloaded tracks.",
)
@passContext
def DownloadCommand(
    ctx: Context, quality: TrackArg | None, template: str | None, noskip: bool
):
    """Download the tracks"""

    api = ctx.obj.getApi()

    def downloadTrack(track: Track, file_name: str, cover_data=b""):
        if not track.allowStreaming:
            click.echo(
                f"{click.style('✖', 'yellow')} Track {click.style(file_name, 'yellow')} does not allow streaming"
            )
            return

        download_quality = ARG_TO_QUALITY[quality or ctx.obj.config.download.quality]

        # .suffix is needed because the Path.with_suffix method will replace any content after dot
        # for example: 'album/01. title' becomes 'album/01.m4a'
        path = ctx.obj.config.download.path / f"{file_name}.suffix"

        if not noskip and trackExists(track.audioQuality, download_quality, path):
            click.echo(
                f"{click.style('✔', 'cyan')} Skipping track {click.style(file_name, 'cyan')}"
            )
            return

        click.echo(
            f"{click.style('✔', 'green')} Downloading track {click.style(file_name, 'green')}"
        )

        track_stream = api.getTrackStream(track.id, download_quality)

        stream_data, file_extension = downloadTrackStream(track_stream)

        full_path = path.with_suffix(file_extension)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with full_path.open("wb") as f:
            f.write(stream_data)

        # TODO: add track credits fetching to fill more metadata

        if not cover_data and track.album.cover:
            cover_data = Cover(track.album.cover).content

        addMetadata(full_path, track, cover_data)

    def downloadAlbum(album: Album):
        click.echo(f"★ Album {album.title}")

        # TODO: fetch all items
        album_items = api.getAlbumItems(album.id, limit=100)

        cover_data = Cover(album.cover).content if album.cover else b""

        for item in album_items.items:
            if isinstance(item.item, Track):
                track = item.item

                file_name = formatTrack(
                    template=template or ctx.obj.config.template.album,
                    track=track,
                    album_artist=album.artist.name,
                )

                downloadTrack(track=track, file_name=file_name, cover_data=cover_data)

    def handleResource(resource: TidalResource):
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

                downloadAlbum(album)

            case "artist":
                # TODO: add `include_singles`
                # TODO: fetch all items
                artist_albums = api.getArtistAlbums(resource.id)

                for album in artist_albums.items:
                    downloadAlbum(album)

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

    for resource in ctx.obj.resources:
        try:
            handleResource(resource)

        except ApiError as e:
            click.echo(click.style(f"✖ {e}", "red"))

        except AuthError as e:
            click.echo(click.style(f"✖ {e}", "red"))


UrlGroup.add_command(DownloadCommand)
SearchGroup.add_command(DownloadCommand)
FavGroup.add_command(DownloadCommand)
FileGroup.add_command(DownloadCommand)
