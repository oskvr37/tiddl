"""Example of concurrent playlist downloading with ThreadPoolExecutor and rich."""

import logging

from pathlib import Path
from requests import Session
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    TaskID,
    BarColumn,
    Progress,
    TextColumn,
)

from tiddl.api import TidalApi
from tiddl.download import parseTrackStream
from tiddl.config import Config
from tiddl.models.api import PlaylistItems
from tiddl.models.resource import Track


WORKERS_COUNT = 4
PLAYLIST_UUID = "84974059-76af-406a-aede-ece2b78fa372"
ALBUM_ID = 103805723

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


def handleTrackDownload(task_id: TaskID, track: Track):
    track_stream = api.getTrackStream(track.id, "HI_RES_LOSSLESS")
    urls, extension = parseTrackStream(track_stream)

    progress.update(task_id, total=len(urls), visible=True)
    progress.start_task(task_id)

    with Session() as s:
        stream_data = b""

        for url in urls:
            req = s.get(url)
            progress.update(task_id, advance=1)
            stream_data += req.content

    path = Path("tracks") / f"{track.title}{extension}"
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("wb") as f:
        f.write(stream_data)

    console.log(track.title)
    progress.remove_task(task_id)


progress.start()

pool = ThreadPoolExecutor(max_workers=WORKERS_COUNT)


def submitTrack(track: Track):
    task_id = progress.add_task(
        description=track.title,
        track=track,
        start=False,
        visible=False,
    )

    pool.submit(handleTrackDownload, task_id=task_id, track=track)


# NOTE: these api requests will run one by one,
# we will need to add some sleep between requests

playlist_items = api.getPlaylistItems(playlist_uuid=PLAYLIST_UUID, limit=5)

for item in playlist_items.items:
    track = item.item

    if isinstance(track, PlaylistItems.PlaylistTrackItem.PlaylistTrack):
        submitTrack(track)

album_items = api.getAlbumItems(album_id=ALBUM_ID, limit=5)

for item in album_items.items:
    track = item.item

    if isinstance(track, Track):
        submitTrack(track)

# cleanup

pool.shutdown(wait=True)
progress.stop()
