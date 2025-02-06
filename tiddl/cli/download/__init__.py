import click

from .fav import FavGroup
from .file import FileGroup
from .search import SearchGroup
from .url import UrlGroup

from ..ctx import Context, passContext

from typing import List, Union, Literal

from tiddl.download import downloadTrackStream
from tiddl.utils import (
    formatTrack,
    trackExists,
    TidalResource,
    convertFileExtension,
)
from tiddl.metadata import addMetadata, Cover
from tiddl.exceptions import ApiError, AuthError
from tiddl.models.constants import TrackArg, ARG_TO_QUALITY
from tiddl.models.resource import Track, Album
from tiddl.models.api import PlaylistItems, AlbumItemsCredits

SinglesFilter = Literal["none", "only", "include"]


@click.command("download")
@click.option(
    "--quality", "-q", "quality", type=click.Choice(TrackArg.__args__)
)
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
@click.option(
    "--singles",
    "-s",
    "singles_filter",
    type=click.Choice(SinglesFilter.__args__),
    default="none",
    help="Defines how to treat artist EPs and singles.",
)
@passContext
def DownloadCommand(
    ctx: Context,
    quality: TrackArg | None,
    template: str | None,
    noskip: bool,
    singles_filter: SinglesFilter = "none",
):
    """Download the tracks"""

    api = ctx.obj.getApi()

    def downloadTrack(
        track: Track,
        file_name: str,
        cover_data=b"",
        credits: List[AlbumItemsCredits.ItemWithCredits.CreditsEntry] = [],
    ):
        if not track.allowStreaming:
            click.echo(
                f"{click.style('✖', 'yellow')} Track {click.style(file_name, 'yellow')} does not allow streaming"
            )
            return

        download_quality = ARG_TO_QUALITY[
            quality or ctx.obj.config.download.quality
        ]

        # .suffix is needed because the Path.with_suffix method will replace any content after dot
        # for example: 'album/01. title' becomes 'album/01.m4a'
        path = ctx.obj.config.download.path / f"{file_name}.suffix"

        if not noskip and trackExists(
            track.audioQuality, download_quality, path
        ):
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

        # extract flac from m4a container

        if track_stream.audioQuality == "HI_RES_LOSSLESS":
            full_path = convertFileExtension(
                full_path, ".flac", remove_source=True
            )

        if not cover_data and track.album.cover:
            cover_data = Cover(track.album.cover).content

        try:
            addMetadata(
                full_path, track, cover_data=cover_data, credits=credits
            )
        except Exception as e:
            click.echo(
                f"{click.style('✖', 'yellow')} Cant set metadata to {click.style(file_name, 'yellow')}. {e}"
            )

    def downloadAlbum(album: Album):
        click.echo(f"★ Album {album.title}")

        all_items: List[
            Union[AlbumItemsCredits.VideoItem, AlbumItemsCredits.TrackItem]
        ] = []
        offset = 0

        while True:
            album_items = api.getAlbumItemsCredits(album.id, offset=offset)
            all_items.extend(album_items.items)

            if (
                album_items.limit + album_items.offset
                > album_items.totalNumberOfItems
            ):
                break

            offset += album_items.limit

        cover_data = Cover(album.cover).content if album.cover else b""

        for item in all_items:
            if isinstance(item.item, Track):
                track = item.item

                file_name = formatTrack(
                    template=template or ctx.obj.config.template.album,
                    track=track,
                    album_artist=album.artist.name,
                )

                downloadTrack(
                    track=track,
                    file_name=file_name,
                    cover_data=cover_data,
                    credits=item.credits,
                )

    def handleResource(resource: TidalResource):
        match resource.type:
            case "track":
                track = api.getTrack(resource.id)
                file_name = formatTrack(
                    template=template or ctx.obj.config.template.track,
                    track=track,
                )

                downloadTrack(
                    track=track,
                    file_name=file_name,
                )

            case "album":
                album = api.getAlbum(resource.id)

                downloadAlbum(album)

            case "artist":

                def getAllAlbums(singles: bool):
                    all_albums: List[Album] = []
                    offset = 0

                    while True:
                        items = api.getArtistAlbums(
                            resource.id,
                            offset=offset,
                            filter="EPSANDSINGLES" if singles else "ALBUMS",
                        )
                        all_albums.extend(items.items)

                        if (
                            items.limit + items.offset
                            > items.totalNumberOfItems
                        ):
                            break

                        offset += items.limit

                    return all_albums

                if singles_filter == "include":
                    albums = getAllAlbums(False) + getAllAlbums(True)
                else:
                    albums = getAllAlbums(singles_filter == "only")

                for album in albums:
                    downloadAlbum(album)

            case "playlist":
                playlist = api.getPlaylist(resource.id)
                click.echo(f"★ Playlist {playlist.title}")

                all_items: List[
                    Union[
                        PlaylistItems.PlaylistVideoItem,
                        PlaylistItems.PlaylistTrackItem,
                    ]
                ] = []
                offset = 0

                while True:
                    items = api.getPlaylistItems(playlist.uuid, offset=offset)
                    all_items.extend(items.items)

                    if items.limit + items.offset > items.totalNumberOfItems:
                        break

                    offset += items.limit

                for item in all_items:
                    if isinstance(
                        item.item, PlaylistItems.PlaylistTrackItem.PlaylistTrack
                    ):
                        track = item.item

                        file_name = formatTrack(
                            template=template
                            or ctx.obj.config.template.playlist,
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
