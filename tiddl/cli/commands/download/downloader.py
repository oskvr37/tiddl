import shutil
import asyncio
import aiohttp
import aiofiles

from logging import getLogger

from pathlib import Path
from tempfile import NamedTemporaryFile

from tiddl.core.api.models import TrackQuality, VideoQuality, Track, Video
from tiddl.core.api import TidalAPI, ApiError
from tiddl.core.utils import parse_track_stream, parse_video_stream
from tiddl.core.utils.ffmpeg import convert_to_mp4, extract_flac
from tiddl.cli.config import (
    TRACK_QUALITY_LITERAL,
    VIDEO_QUALITY_LITERAL,
    VIDEOS_FILTER_LITERAL,
)
from tiddl.cli.utils.download import get_existing_track_filename

from .output import RichOutput

log = getLogger(__name__)

CHUNK_SIZE = 1024**2

track_qualities: dict[TRACK_QUALITY_LITERAL, TrackQuality] = {
    "low": "LOW",
    "normal": "HIGH",
    "high": "LOSSLESS",
    "max": "HI_RES_LOSSLESS",
}

track_qualities_color: dict[TrackQuality, str] = {
    "LOW": "[gray]96 kbps",
    "HIGH": "[gray]320 kbps",
    "LOSSLESS": "[cyan]",
    "HI_RES_LOSSLESS": "[yellow]",
}

video_qualities: dict[VIDEO_QUALITY_LITERAL, VideoQuality] = {
    "sd": "LOW",
    "hd": "MEDIUM",
    "fhd": "HIGH",
}

video_qualities_color: dict[VideoQuality, str] = {
    "LOW": "[gray]360p",
    "MEDIUM": "[cyan]720p",
    "HIGH": "[yellow]1080p",
}


class Downloader:
    api: TidalAPI
    rich_output: RichOutput
    semaphore: asyncio.Semaphore
    track_quality: TrackQuality
    video_quality: VideoQuality
    videos_filter: VIDEOS_FILTER_LITERAL
    skip_existing: bool
    download_path: Path
    scan_path: Path

    def __init__(
        self,
        tidal_api: TidalAPI,
        threads_count: int,
        rich_output: RichOutput,
        track_quality: TRACK_QUALITY_LITERAL,
        video_quality: VIDEO_QUALITY_LITERAL,
        videos_filter: VIDEOS_FILTER_LITERAL,
        skip_existing: bool,
        download_path: Path,
        scan_path: Path,
    ) -> None:
        self.api = tidal_api
        self.rich_output = rich_output
        self.semaphore = asyncio.Semaphore(threads_count)
        self.track_quality = track_qualities[track_quality]
        self.video_quality = video_qualities[video_quality]
        self.videos_filter = videos_filter
        self.skip_existing = skip_existing
        self.download_path = download_path
        self.scan_path = scan_path

    async def download(
        self, item: Track | Video, file_path: Path
    ) -> tuple[Path | None, bool]:
        """
        returns
        - Path `item_path` path of existing/downloaded item
        - bool `was_downloaded`
        """

        if not item.allowStreaming:
            self.rich_output.console.print(
                f"[red]Can't stream[/] {item.title} ({item.id})"
            )
            return None, False

        if isinstance(item, Track):
            filename = get_existing_track_filename(
                item.audioQuality, self.track_quality, file_path
            )
            vibrant_color = item.album.vibrantColor

        elif isinstance(item, Video):
            filename = file_path.with_suffix(".mp4")
            vibrant_color = item.vibrantColor

        vibrant_color = vibrant_color or "gray"

        existing_file_path = self.scan_path / filename

        log.debug(f"{file_path=}, {filename=}, {existing_file_path=}")

        result_message = "[green]Downloaded"

        if existing_file_path.exists():
            result_message = "[cyan]Overwrited"

            if self.skip_existing:
                self.rich_output.show_item_result(
                    result_message="[yellow]Exists",
                    item_description=f"[{vibrant_color}]{item.title}",
                    item_path=existing_file_path,
                )
                return existing_file_path, False

        elif (isinstance(item, Video) and self.videos_filter == "none") or (
            isinstance(item, Track) and self.videos_filter == "only"
        ):
            log.info(f"skipping {item.id} due to {self.videos_filter=}")
            return None, False

        should_extract_flac = False

        async with self.semaphore:
            if isinstance(item, Track):
                try:
                    stream = self.api.get_track_stream(
                        track_id=item.id, quality=self.track_quality
                    )
                except ApiError as e:
                    log.error(f"{item.id=} {e=}")
                    self.rich_output.console.print(
                        f"[red]Error [{vibrant_color}]{item.title}[/] - {e.user_message}"
                    )
                    return None, False

                urls, _ = parse_track_stream(stream)
                download_path = self.download_path / filename

                quality = track_qualities_color[stream.audioQuality]

                if stream.audioQuality in ["HI_RES_LOSSLESS", "LOSSLESS"]:
                    quality = f"{quality} {stream.bitDepth}-bit, {(stream.sampleRate or 0) / 1000:.1f} kHz"

                if stream.audioQuality == "HI_RES_LOSSLESS":
                    should_extract_flac = True

            elif isinstance(item, Video):
                stream = self.api.get_video_stream(
                    video_id=item.id, quality=self.video_quality
                )

                urls, ext = parse_video_stream(stream), ".ts"
                download_path = (self.download_path / filename).with_suffix(ext)
                quality = video_qualities_color[stream.videoQuality]

            task_id = self.rich_output.download_start(
                f"[{vibrant_color}]{item.title} {quality}"
            )

            download_path.parent.mkdir(exist_ok=True, parents=True)

            # TODO shouldnt session be reused instead of
            # creating new one on every download?

            with NamedTemporaryFile(
                "wb", delete=False, dir=download_path.parent
            ) as tmp:
                async with aiohttp.ClientSession() as session:
                    async with aiofiles.open(tmp.name, "wb") as f:
                        for url in urls:
                            async with session.get(url) as resp:
                                async for chunk in resp.content.iter_chunked(
                                    CHUNK_SIZE
                                ):
                                    await f.write(chunk)
                                    self.rich_output.download_advance(
                                        task_id, size=len(chunk)
                                    )

            shutil.move(tmp.name, download_path)

            try:
                if isinstance(item, Track) and should_extract_flac:
                    download_path = extract_flac(download_path)
                elif isinstance(item, Video):
                    download_path = convert_to_mp4(download_path)
            except Exception as exc:
                log.error(f"{should_extract_flac=}, {exc=}")

            task = self.rich_output.download_finish(
                task_id=task_id,
            )

            self.rich_output.show_item_result(
                result_message=result_message,
                item_description=task.description,
                item_path=download_path,
            )

            return download_path, True
