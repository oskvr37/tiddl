import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Literal, Union

import click
from requests import Session
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
)

from tiddl.download import parseTrackStream, parseVideoStream
from tiddl.exceptions import ApiError, AuthError
from tiddl.metadata import Cover, addMetadata
from tiddl.models.api import AlbumItemsCredits, PlaylistItems
from tiddl.models.constants import ARG_TO_QUALITY, TrackArg
from tiddl.models.resource import Track, Video
from tiddl.utils import (
    TidalResource,
    convertFileExtension,
    formatResource,
    trackExists,
)

from ..ctx import Context, passContext

SinglesFilter = Literal["none", "only", "include"]


@click.command("download")
@click.option(
    "--quality", "-q", "QUALITY", type=click.Choice(TrackArg.__args__)
)
@click.option(
    "--output", "-o", "TEMPLATE", type=str, help="Format track file template."
)
@click.option(
    "--threads",
    "-t",
    "THREADS_COUNT",
    type=int,
    help="Number of threads to use in concurrent download; use with caution.",
    default=1,
)
@click.option(
    "--noskip",
    "-ns",
    "DO_NOT_SKIP",
    is_flag=True,
    default=False,
    help="Do not skip already downloaded tracks.",
)
@click.option(
    "--singles",
    "-s",
    "SINGLES_FILTER",
    type=click.Choice(SinglesFilter.__args__),
    default="none",
    help="Defines how to treat artist EPs and singles.",
)
@passContext
def DownloadCommand(
    ctx: Context,
    QUALITY: TrackArg | None,
    TEMPLATE: str | None,
    THREADS_COUNT: int,
    DO_NOT_SKIP: bool,
    SINGLES_FILTER: SinglesFilter,
):
    """Download resources"""

    # TODO: pretty print
    logging.debug(
        (QUALITY, TEMPLATE, THREADS_COUNT, DO_NOT_SKIP, SINGLES_FILTER)
    )

    DOWNLOAD_QUALITY = ARG_TO_QUALITY[
        QUALITY or ctx.obj.config.download.quality
    ]

    api = ctx.obj.getApi()

    progress = Progress(
        TextColumn("{task.description}"),
        BarColumn(bar_width=40),
        console=ctx.obj.console,
        transient=True,
        auto_refresh=True,
    )

    def handleItemDownload(
        item: Union[Track, Video],
        path: Path,
        cover_data=b"",
        credits: List[AlbumItemsCredits.ItemWithCredits.CreditsEntry] = [],
    ):
        if isinstance(item, Track):
            track_stream = api.getTrackStream(item.id, quality=DOWNLOAD_QUALITY)
            logging.info(
                f"★ Track: {item.title}"
                f" {(str(track_stream.bitDepth) + ' bit') if track_stream.bitDepth else ''} "
                f" {str(track_stream.sampleRate) + ' kHz' if track_stream.sampleRate else ''}"
            )

            urls, extension = parseTrackStream(track_stream)
        elif isinstance(item, Video):
            video_stream = api.getVideoStream(item.id)
            logging.info(
                f"★ Video: {item.title} {video_stream.videoQuality} quality"
            )

            urls = parseVideoStream(video_stream)
            extension = ".ts"
        else:
            raise TypeError(
                f"Invalid item type: expected an instance of Track or Video, "
                f"received an instance of {type(item).__name__}. "
            )

        task_id = progress.add_task(
            description=f"{type(item).__name__}: {item.title}",
            start=True,
            visible=True,
            total=len(urls),
        )

        with Session() as s:
            stream_data = b""

            for url in urls:
                req = s.get(url)

                assert req.status_code == 200, (
                    f"Could not download stream data for: "
                    f"{type(item).__name__} '{item.title}', "
                    f"status code: {req.status_code}"
                )
                
                stream_data += req.content
                progress.advance(task_id)

        path = path.with_suffix(extension)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("wb") as f:
            f.write(stream_data)

        if isinstance(item, Track):
            if item.audioQuality == "HI_RES_LOSSLESS":
                convertFileExtension(
                    source_file=path,
                    extension=".flac",
                    remove_source=True,
                    is_video=False,
                    copy_audio=True,  # extract flac from m4a container
                )

            if not cover_data and item.album.cover:
                cover_data = Cover(item.album.cover).content

            try:
                addMetadata(path, item, cover_data, credits)
            except Exception as e:
                logging.error(f"Can not add metadata to: {path}, {e}")

        elif isinstance(item, Video):
            convertFileExtension(
                source_file=path,
                extension=".mp4",
                remove_source=True,
                is_video=True,
                copy_audio=True,
            )

            # TODO: add metadata

        progress.remove_task(task_id)
        logging.info(f'✔ "{item.title}"')

    pool = ThreadPoolExecutor(max_workers=THREADS_COUNT)

    def submitItem(item: Union[Track, Video], filename: str):
        if not item.allowStreaming:
            logging.warning(
                f"✖ {type(item).__name__}: {item.title} does not allow streaming"
            )
            return

        path = ctx.obj.config.download.path / f"{filename}.*"

        if not DO_NOT_SKIP:  # check if item is already downloaded
            if isinstance(item, Track):
                if trackExists(item.audioQuality, DOWNLOAD_QUALITY, path):
                    logging.debug(f"✖ Skipping Track: {item.title}")
                    return
            elif isinstance(item, Video):
                if path.with_suffix(".mp4").exists():
                    logging.debug(f"✖ Skipping Video: {item.title}")
                    return

        # TODO: cover, credits
        future = pool.submit(
            handleItemDownload, item=item, path=path, cover_data=b"", credits=[]
        )
        try:
            future.result()
        except Exception as e:
            logging.error(e)

    def handleResource(resource: TidalResource) -> None:
        logging.debug(f"Handling Resource {resource}")

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
                logging.info(f"★ Album: {album.title}")
                pass

            case "artist":
                artist = api.getArtist(resource.id)
                logging.info(f"★ Artist: {artist.name}")
                pass

            case "playlist":
                playlist = api.getPlaylist(resource.id)
                logging.info(f"★ Playlist: {playlist.title}")
                pass

    progress.start()

    # TODO: remove this
    ctx.obj.resources.extend(
        [
            TidalResource(type="track", id="103805726"),
            TidalResource(type="album", id="103805723"),
        ]
    )

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
