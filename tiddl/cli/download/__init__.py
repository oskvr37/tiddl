import logging
import click

from .fav import FavGroup
from .file import FileGroup
from .search import SearchGroup
from .url import UrlGroup

from ..ctx import Context, passContext

from typing import List, Literal

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
            logging.warning(f"Track {file_name} does not allow streaming")
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
            logging.info(f"Skipping track {file_name}")
            return

        logging.info(f"Downloading track {file_name}")

        track_stream = api.getTrackStream(track.id, download_quality)

        stream_data, file_extension = downloadTrackStream(track_stream)

        full_path = path.with_suffix(file_extension)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with full_path.open("wb") as f:
            f.write(stream_data)

        # extract flac from m4a container

        if track_stream.audioQuality == "HI_RES_LOSSLESS":
            full_path = convertFileExtension(
                full_path, ".flac", remove_source=True, copy_audio=True
            )

        if not cover_data and track.album.cover:
            cover_data = Cover(track.album.cover).content

        try:
            addMetadata(
                full_path, track, cover_data=cover_data, credits=credits
            )
        except Exception as e:
            logging.error(f"Cant set metadata to {file_name}: {e}")

    def downloadAlbum(album: Album):
        logging.info(f"Album {album.title}")
        cover_data = Cover(album.cover).content if album.cover else b""

        offset = 0

        while True:
            album_items = api.getAlbumItemsCredits(album.id, offset=offset)
            for item in album_items.items:
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

            if (
                album_items.limit + album_items.offset
                > album_items.totalNumberOfItems
            ):
                break

            offset += album_items.limit

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
                    offset = 0

                    while True:
                        artist_albums = api.getArtistAlbums(
                            resource.id,
                            offset=offset,
                            filter="EPSANDSINGLES" if singles else "ALBUMS",
                        )

                        for album in artist_albums.items:
                            downloadAlbum(album)

                        if (
                            artist_albums.limit + artist_albums.offset
                            > artist_albums.totalNumberOfItems
                        ):
                            break

                        offset += artist_albums.limit

                if singles_filter == "include":
                    getAllAlbums(False)
                    getAllAlbums(True)
                else:
                    getAllAlbums(singles_filter == "only")

            case "playlist":
                playlist = api.getPlaylist(resource.id)
                logging.info(f"Playlist {playlist.title}")

                offset = 0

                while True:
                    playlist_items = api.getPlaylistItems(
                        playlist.uuid, offset=offset
                    )

                    for item in playlist_items.items:
                        if isinstance(
                            item.item,
                            PlaylistItems.PlaylistTrackItem.PlaylistTrack,
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

                    if (
                        playlist_items.limit + playlist_items.offset
                        > playlist_items.totalNumberOfItems
                    ):
                        break

                    offset += playlist_items.limit

    for resource in ctx.obj.resources:
        try:
            handleResource(resource)

        except ApiError as e:
            logging.error(e)

        except AuthError as e:
            logging.error(e)
            return


UrlGroup.add_command(DownloadCommand)
SearchGroup.add_command(DownloadCommand)
FavGroup.add_command(DownloadCommand)
FileGroup.add_command(DownloadCommand)
