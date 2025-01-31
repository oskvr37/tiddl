"""Example of concurrent playlist downloading with ThreadPoolExecutor and rich."""

import logging

from time import sleep
from random import randint
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
from tiddl.config import Config
from tiddl.models.api import PlaylistItems
from tiddl.models.resource import Track


if __name__ == "__main__":
    WORKERS_COUNT = 4
    PLAYLIST_UUID = "84974059-76af-406a-aede-ece2b78fa372"
    ALBUM_ID = 103805723

    console = Console()
    logging.basicConfig(
        level=logging.DEBUG, handlers=[RichHandler(console=console)]
    )

    logging.getLogger("urllib3").setLevel(logging.ERROR)

    config = Config.fromFile()  # load config from default directory

    api = TidalApi(
        config.auth.token, config.auth.user_id, config.auth.country_code
    )

    with Progress(
        TextColumn("{task.description}"),
        BarColumn(bar_width=None),
        console=console,
        transient=True,
    ) as progress:

        def handleTrackDownload(task_id: TaskID, track: Track):
            total = randint(10, 30)
            progress.update(task_id, total=total, visible=True)

            # simulate track download

            for _ in range(total):
                sleep(0.1)
                progress.advance(task_id, 1)

            console.log(track.title)

            progress.remove_task(task_id)

        with ThreadPoolExecutor(max_workers=WORKERS_COUNT) as pool:

            def submitTrack(track: Track):
                task_id = progress.add_task(
                    description=track.title,
                    track=track,
                    start=False,
                    visible=False,
                )

                pool.submit(handleTrackDownload, task_id=task_id, track=track)

            playlist_items = api.getPlaylistItems(
                playlist_uuid=PLAYLIST_UUID, limit=25
            )

            for item in playlist_items.items:
                track = item.item

                if isinstance(
                    track, PlaylistItems.PlaylistTrackItem.PlaylistTrack
                ):
                    submitTrack(track)

            album_items = api.getAlbumItems(album_id=ALBUM_ID, limit=14)

            for item in album_items.items:
                track = item.item

                if isinstance(track, Track):
                    submitTrack(track)

            # NOTE: these api requests will run one by one,
            # we will need to add some sleep between requests
