"""
Example of concurrent album + playlist downloading with ThreadPoolExecutor and rich.
This will download tracks and videos.
"""

import logging

from typing import Union

from pathlib import Path
from requests import Session
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
)

from tiddl.api import TidalApi
from tiddl.download import parseTrackStream, parseVideoStream
from tiddl.config import Config
from tiddl.models.resource import Track, Video
from tiddl.utils import convertFileExtension


WORKERS_COUNT = 4
PLAYLIST_UUID = "84974059-76af-406a-aede-ece2b78fa372"
ALBUM_ID = 103805723
QUALITY = "HI_RES_LOSSLESS"

console = Console()
logging.basicConfig(
    level=logging.DEBUG, handlers=[RichHandler(console=console)]
)

logging.getLogger("urllib3").setLevel(logging.ERROR)

config = Config.fromFile()  # load config from default directory

api = TidalApi(config.auth.token, config.auth.user_id, config.auth.country_code)

progress = Progress(
    TextColumn("{task.description}"),
    BarColumn(bar_width=40),
    console=console,
    transient=True,
    auto_refresh=True,
)


def handleItemDownload(item: Union[Track, Video]):
    if isinstance(item, Track):
        track_stream = api.getTrackStream(item.id, quality=QUALITY)
        urls, extension = parseTrackStream(track_stream)
    elif isinstance(item, Video):
        video_stream = api.getVideoStream(item.id)
        urls = parseVideoStream(video_stream)
        extension = ".ts"
    else:
        raise TypeError(
            f"Invalid item type: expected an instance of Track or Video, "
            f"received an instance of {type(item).__name__}. "
        )

    task_id = progress.add_task(
        description=f"{type(item).__name__} {item.title}",
        start=True,
        visible=True,
        total=len(urls),
    )

    with Session() as s:
        stream_data = b""

        for url in urls:
            req = s.get(url)
            stream_data += req.content
            progress.advance(task_id)

    path = Path("examples") / "downloads" / f"{item.id}{extension}"
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

    elif isinstance(item, Video):
        convertFileExtension(
            source_file=path,
            extension=".mp4",
            remove_source=True,
            is_video=True,
            copy_audio=True,
        )

    console.log(item.title)
    progress.remove_task(task_id)


progress.start()

pool = ThreadPoolExecutor(max_workers=WORKERS_COUNT)


def submitItem(item: Union[Track, Video]):
    pool.submit(handleItemDownload, item=item)


# NOTE: these api requests will run one by one,
# we will need to add some sleep between requests

playlist_items = api.getPlaylistItems(playlist_uuid=PLAYLIST_UUID, limit=10)

for item in playlist_items.items:
    submitItem(item.item)

album_items = api.getAlbumItems(album_id=ALBUM_ID, limit=5)

for item in album_items.items:
    submitItem(item.item)

# cleanup

pool.shutdown(wait=True)
progress.stop()
