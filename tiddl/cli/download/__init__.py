import logging
import click
import asyncio

from time import perf_counter
from concurrent.futures import ThreadPoolExecutor, Future
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
    savePlaylistM3U,
    findTrackFilename,
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
@click.option(
    "--lyrics",
    "-l",
    "EMBED_LYRICS",
    is_flag=True,
    help="Embed track lyrics in file metadata.",
)
@click.option(
    "--video",
    "-V",
    "DOWNLOAD_VIDEO",
    is_flag=True,
    help="Enable downloading videos",
)
@click.option(
    "--scan-path",
    "SCAN_PATH",
    type=str,
    help="Base directory to scan for existing tracks. Default is 'path'",
)
@click.option(
    "--save-m3u",
    "-m3u",
    "SAVE_M3U",
    is_flag=True,
    help="Save M3U file for playlists.",
)
@passContext
def DownloadCommand(
    ctx: Context,
    QUALITY: TrackArg | None,
    TEMPLATE: str | None,
    PATH: str | None,
    THREADS_COUNT: int | None,
    DO_NOT_SKIP: bool,
    SINGLES_FILTER: SinglesFilter,
    EMBED_LYRICS: bool,
    DOWNLOAD_VIDEO: bool,
    SCAN_PATH: str | None,
    SAVE_M3U: bool,
):
    """Download resources"""
    DOWNLOAD_VIDEO = DOWNLOAD_VIDEO or ctx.obj.config.download.download_video
    SINGLES_FILTER = SINGLES_FILTER or ctx.obj.config.download.singles_filter
    EMBED_LYRICS = EMBED_LYRICS or ctx.obj.config.download.embed_lyrics

    # TODO: pretty print
    logging.debug(
        (
            QUALITY,
            TEMPLATE,
            PATH,
            THREADS_COUNT,
            DO_NOT_SKIP,
            SINGLES_FILTER,
            EMBED_LYRICS,
            DOWNLOAD_VIDEO,
            SCAN_PATH,
            SAVE_M3U,
        )
    )

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
    ) -> Path:
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
                path = asyncio.run(
                    convertFileExtension(
                        source_file=path,
                        extension=".flac",
                        remove_source=True,
                        is_video=False,
                        copy_audio=True,  # extract flac from m4a container
                    )
                )

            if not cover_data and item.album.cover:
                cover_data = Cover(item.album.cover).content

            if EMBED_LYRICS:
                lyrics_subtitles = api.getLyrics(item.id).subtitles
            else:
                lyrics_subtitles = ""

            try:
                addMetadata(
                    path,
                    item,
                    cover_data,
                    credits,
                    album_artist=album_artist,
                    lyrics=lyrics_subtitles,
                )
            except Exception as e:
                logging.error(f"Can not add metadata to: {path}, {e}")

        elif isinstance(item, Video):
            path = asyncio.run(
                convertFileExtension(
                    source_file=path,
                    extension=".mp4",
                    remove_source=True,
                    is_video=True,
                    copy_audio=True,
                )
            )

            try:
                addVideoMetadata(path, item)
            except Exception as e:
                logging.error(f"Can not add metadata to: {path}, {e}")

        progress.remove_task(task_id)
        logging.info(f"{item.title!r} • {speed:.2f} Mbps • {size:.2f} MB")

        return path

    pool = ThreadPoolExecutor(
        max_workers=THREADS_COUNT or ctx.obj.config.download.threads
    )

    def submitItem(
        item: Union[Track, Video],
        filename: str,
        cover_data=b"",
        credits: List[AlbumItemsCredits.ItemWithCredits.CreditsEntry] = [],
        album_artist="",
    ) -> Future[Path] | None:
        if not item.allowStreaming:
            logging.warning(
                f"✖ {type(item).__name__} '{item.title}' does not allow streaming"
            )
            return

        download_path = Path(PATH) if PATH else ctx.obj.config.download.path
        download_path /= f"{filename}.*"

        scan_path = Path(SCAN_PATH) if SCAN_PATH else ctx.obj.config.download.scan_path
        if scan_path:
            scan_path /= f"{filename}.*"
        else:
            scan_path = download_path

        # Respect DOWNLOAD_VIDEO = FALSE over DO_NOT_SKIP (as it's for the file exists check)
        if isinstance(item, Video) and not DOWNLOAD_VIDEO:
            logging.warning(f"Video '{item.title}' skipped as DOWNLOAD_VIDEO is false")
            return

        # check if item is already downloaded (unless DO_NOT_SKIP is set, then override anything)
        if not DO_NOT_SKIP:
            if isinstance(item, Track):
                track_path = findTrackFilename(
                    item.audioQuality, DOWNLOAD_QUALITY, scan_path
                )
                if track_path.exists():
                    logging.info(f"Track '{item.title}' skipped - exists")
                    future = Future()
                    future.set_result(track_path)
                    return future

            elif isinstance(item, Video):
                if scan_path.with_suffix(".mp4").exists():
                    logging.info(f"Video '{item.title}' skipped - exists")
                    return

        future = pool.submit(
            handleItemDownload,
            item=item,
            path=download_path,
            cover_data=cover_data,
            credits=credits,
            album_artist=album_artist,
        )

        return future

    def downloadAlbum(album: Album):
        logging.info(f"Album {album.title!r}")

        cover = (
            Cover(uid=album.cover, size=ctx.obj.config.cover.size)
            if album.cover
            else None
        )
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

                if cover and not is_cover_saved and ctx.obj.config.cover.save:
                    path = Path(PATH) if PATH else ctx.obj.config.download.path
                    cover_path = path / Path(filename).parent
                    cover.save(cover_path, ctx.obj.config.cover.filename)
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
        logging.debug(f"'{resource}'")

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

            case "mix":
                mix = api.getMix(resource.id)

                for mix_item in mix.items:
                    filename = formatResource(
                        TEMPLATE or ctx.obj.config.template.track, mix_item.item
                    )

                    submitItem(mix_item.item, filename)

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
                logging.info(f"downloading playlist {playlist.title!r}")
                offset = 0
                playlist_path = None

                futures: list[tuple[Future[Path], Track]] = []

                while True:
                    playlist_items = api.getPlaylistItems(playlist.uuid, offset=offset)

                    for item in playlist_items.items:
                        filename = formatResource(
                            template=TEMPLATE or ctx.obj.config.template.playlist,
                            resource=item.item,
                            playlist_title=playlist.title,
                            playlist_index=item.item.index // 100000,
                        )

                        future = submitItem(item.item, filename)
                        if future:
                            futures.append((future, item.item))

                        playlist_path = Path(filename).parent

                    if (
                        playlist_items.limit + playlist_items.offset
                        > playlist_items.totalNumberOfItems
                    ):
                        break

                    offset += playlist_items.limit

                playlist_tracks: list[tuple[Path, Track]] = []
                for future, track in futures:
                    track_path = future.result()
                    playlist_tracks.append((track_path, track))

                path = Path(PATH) if PATH else ctx.obj.config.download.path

                if playlist_path and (SAVE_M3U or ctx.obj.config.download.save_playlist_m3u):
                    savePlaylistM3U(
                        playlist_tracks=playlist_tracks,
                        path=path / playlist_path,
                        filename=f"{playlist.title}.m3u",
                    )

                if playlist.squareImage and playlist_path:
                    cover = Cover(
                        uid=playlist.squareImage,
                        size=1080,  # playlist cover must be 1080x1080
                    )
                    cover.save(path / playlist_path, ctx.obj.config.cover.filename)

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
