import logging
import click

from time import perf_counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from requests import Session

from rich.highlighter import ReprHighlighter
from rich.progress import (
    SpinnerColumn,
    Progress,
    TextColumn,
)

from tiddl.download import parseTrackStream, parseVideoStream
from tiddl.exceptions import ApiError, AuthError
from tiddl.metadata import Cover, addMetadata, addVideoMetadata
from tiddl.models.api import AlbumItemsCredits
from tiddl.models.constants import ARG_TO_QUALITY, TrackArg, SinglesFilter
from tiddl.models.resource import Track, Video, Album
from tiddl.utils import (
    TidalResource,
    formatResource,
    convertFileExtension,
    trackExists,
)

from tiddl.cli.ctx import Context, passContext
from tiddl.cli.download.fav import FavGroup
from tiddl.cli.download.file import FileGroup
from tiddl.cli.download.search import SearchGroup
from tiddl.cli.download.url import UrlGroup

from typing import List, Union


@click.command("download")
@click.option(
    "--quality",
    "-q",
    "QUALITY",
    type=click.Choice(TrackArg.__args__),
    help="Track quality.",
)
@click.option(
    "--output",
    "-o",
    "TEMPLATE",
    type=str,
    help="Format output file template. "
    "This will be used instead of your config templates.",
)
@click.option(
    "--path",
    "-p",
    "PATH",
    type=str,
    help="Base path of download directory. Default is ~/Music/Tiddl.",
)
@click.option(
    "--threads",
    "-t",
    "THREADS_COUNT",
    type=int,
    help="Number of threads to use in concurrent download; use with caution.",
)
@click.option(
    "--noskip",
    "-ns",
    "DO_NOT_SKIP",
    is_flag=True,
    default=False,
    help="Do not skip already downloaded files.",
)
@click.option(
    "--singles",
    "-s",
    "SINGLES_FILTER",
    type=click.Choice(SinglesFilter.__args__),
    help="Defines how to treat artist EPs and singles, used while downloading artist.",
)
@passContext
def DownloadCommand(
    ctx: Context,
    QUALITY: TrackArg | None,
    TEMPLATE: str | None,
    PATH: str | None,
    THREADS_COUNT: int,
    DO_NOT_SKIP: bool,
    SINGLES_FILTER: SinglesFilter,
):
    """Download resources"""

    SINGLES_FILTER = SINGLES_FILTER or ctx.obj.config.download.singles_filter

    # TODO: pretty print
    logging.debug((QUALITY, TEMPLATE, PATH, THREADS_COUNT, DO_NOT_SKIP, SINGLES_FILTER))

    DOWNLOAD_QUALITY = ARG_TO_QUALITY[QUALITY or ctx.obj.config.download.quality]

    api = ctx.obj.getApi()

    progress = Progress(
        SpinnerColumn(),
        TextColumn(
            "{task.description} • "
            "{task.fields[speed]:.2f} Mbps • {task.fields[size]:.2f} MB",
            highlighter=ReprHighlighter(),
        ),
        console=ctx.obj.console,
        transient=True,
        auto_refresh=True,
    )

    def handleItemDownload(
        item: Union[Track, Video],
        path: Path,
        cover_data=b"",
        credits: List[AlbumItemsCredits.ItemWithCredits.CreditsEntry] = [],
        album_artist="",
    ):
        if isinstance(item, Track):
            track_stream = api.getTrackStream(item.id, quality=DOWNLOAD_QUALITY)
            description = (
                f"Track '{item.title}' "
                f"{(str(track_stream.bitDepth) + ' bit') if track_stream.bitDepth else ''} "
                f"{str(track_stream.sampleRate) + ' kHz' if track_stream.sampleRate else ''}"
            )

            urls, extension = parseTrackStream(track_stream)
        elif isinstance(item, Video):
            video_stream = api.getVideoStream(item.id)
            description = f"Video '{item.title}' {video_stream.videoQuality} quality"

            urls = parseVideoStream(video_stream)
            extension = ".ts"
        else:
            raise TypeError(
                f"Invalid item type: expected an instance of Track or Video, "
                f"received an instance of {type(item).__name__}. "
            )

        task_id = progress.add_task(
            description=description,
            start=True,
            visible=True,
            total=None,
            # fields
            speed=0,
            size=0,
        )

        with Session() as s:
            stream_data = b""
            time_start = perf_counter()

            for url in urls:
                req = s.get(url)

                assert req.status_code == 200, (
                    f"Could not download stream data for: "
                    f"{type(item).__name__} '{item.title}', "
                    f"status code: {req.status_code}"
                )

                stream_data += req.content
                speed = len(stream_data) / (perf_counter() - time_start) / (1024 * 128)
                size = len(stream_data) / 1024**2
                progress.update(
                    task_id,
                    advance=len(req.content),
                    speed=speed,
                    size=size,
                )

        path = path.with_suffix(extension)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("wb") as f:
            f.write(stream_data)

        if isinstance(item, Track):
            if track_stream.audioQuality == "HI_RES_LOSSLESS":
                path = convertFileExtension(
                    source_file=path,
                    extension=".flac",
                    remove_source=True,
                    is_video=False,
                    copy_audio=True,  # extract flac from m4a container
                )

            if not cover_data and item.album.cover:
                cover_data = Cover(item.album.cover).content

            try:
                addMetadata(path, item, cover_data, credits, album_artist=album_artist)
            except Exception as e:
                logging.error(f"Can not add metadata to: {path}, {e}")

        elif isinstance(item, Video):
            path = convertFileExtension(
                source_file=path,
                extension=".mp4",
                remove_source=True,
                is_video=True,
                copy_audio=True,
            )

            try:
                addVideoMetadata(path, item)
            except Exception as e:
                logging.error(f"Can not add metadata to: {path}, {e}")

        progress.remove_task(task_id)
        logging.info(f"{item.title!r} • {speed:.2f} Mbps • {size:.2f} MB")

    pool = ThreadPoolExecutor(
        max_workers=THREADS_COUNT or ctx.obj.config.download.threads
    )

    def submitItem(
        item: Union[Track, Video],
        filename: str,
        cover_data=b"",
        credits: List[AlbumItemsCredits.ItemWithCredits.CreditsEntry] = [],
        album_artist="",
    ):
        if not item.allowStreaming:
            logging.warning(
                f"✖ {type(item).__name__} '{item.title}' does not allow streaming"
            )
            return

        path = Path(PATH) if PATH else ctx.obj.config.download.path
        path /= f"{filename}.*"

        if not DO_NOT_SKIP:  # check if item is already downloaded
            if isinstance(item, Track):
                if trackExists(item.audioQuality, DOWNLOAD_QUALITY, path):
                    logging.warning(f"Track '{item.title}' skipped")
                    return
            elif isinstance(item, Video):
                if path.with_suffix(".mp4").exists():
                    logging.warning(f"Video '{item.title}' skipped")
                    return

        pool.submit(
            handleItemDownload,
            item=item,
            path=path,
            cover_data=cover_data,
            credits=credits,
            album_artist=album_artist,
        )

    def downloadAlbum(album: Album):
        logging.info(f"Album {album.title!r}")

        cover = Cover(uid=album.cover, size=COVER_SIZE) if album.cover else None
        is_cover_saved = False

        offset = 0

        while True:
            album_items = api.getAlbumItemsCredits(album.id, offset=offset)

            for item in album_items.items:
                filename = formatResource(
                    template=TEMPLATE or ctx.obj.config.template.album,
                    resource=item.item,
                    album_artist=album.artist.name,
                )

                if cover and not is_cover_saved and SAVE_COVERS:
                    path = Path(PATH) if PATH else ctx.obj.config.download.path
                    cover_path = path / Path(filename).parent
                    cover.save(cover_path)
                    is_cover_saved = True

                submitItem(
                    item.item,
                    filename,
                    cover.content if cover else b"",
                    item.credits,
                    album.artist.name,
                )

            if album_items.limit + album_items.offset > album_items.totalNumberOfItems:
                break

            offset += album_items.limit

    def handleResource(resource: TidalResource) -> None:
        logging.debug(f"Handling Resource '{resource}'")

        match resource.type:
            case "track":
                track = api.getTrack(resource.id)
                filename = formatResource(
                    TEMPLATE or ctx.obj.config.template.track, track
                )

                submitItem(track, filename)

            case "video":
                video = api.getVideo(resource.id)
                filename = formatResource(
                    TEMPLATE or ctx.obj.config.template.video, video
                )

                submitItem(video, filename)

            case "album":
                album = api.getAlbum(resource.id)

                downloadAlbum(album)

            case "artist":
                artist = api.getArtist(resource.id)
                logging.info(f"Artist {artist.name!r}")

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

                if SINGLES_FILTER == "include":
                    getAllAlbums(False)
                    getAllAlbums(True)
                else:
                    getAllAlbums(SINGLES_FILTER == "only")

            case "playlist":
                playlist = api.getPlaylist(resource.id)
                logging.info(f"Playlist {playlist.title!r}")
                offset = 0

                while True:
                    playlist_items = api.getPlaylistItems(playlist.uuid, offset=offset)

                    for item in playlist_items.items:
                        filename = formatResource(
                            template=TEMPLATE or ctx.obj.config.template.playlist,
                            resource=item.item,
                            playlist_title=playlist.title,
                            playlist_index=item.item.index // 100000,
                        )

                        submitItem(item.item, filename)

                    if (
                        playlist_items.limit + playlist_items.offset
                        > playlist_items.totalNumberOfItems
                    ):
                        break

                    offset += playlist_items.limit

    progress.start()

    # TODO: make sure every resource is unique
    for resource in ctx.obj.resources:
        try:
            handleResource(resource)

        except AuthError as e:
            logging.error(e)
            break

        except ApiError as e:
            logging.error(e)

            # session does not have streaming privileges
            if e.sub_status == 4006:
                break

    pool.shutdown(wait=True)
    progress.stop()


UrlGroup.add_command(DownloadCommand)
SearchGroup.add_command(DownloadCommand)
FavGroup.add_command(DownloadCommand)
FileGroup.add_command(DownloadCommand)
