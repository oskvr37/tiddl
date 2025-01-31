"""Example of concurrent playlist downloading with ThreadPoolExecutor and rich."""

from time import sleep
from random import randint
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
)

from tiddl.api import TidalApi
from tiddl.config import Config
from tiddl.models.api import PlaylistItems
from tiddl.models.resource import Track


if __name__ == "__main__":
    PLAYLIST_UUID = "84974059-76af-406a-aede-ece2b78fa372"
    WORKERS_COUNT = 3

    config = Config.fromFile()  # load config from default directory

    api = TidalApi(
        config.auth.token, config.auth.user_id, config.auth.country_code
    )

    playlist_items = api.getPlaylistItems(playlist_uuid=PLAYLIST_UUID, limit=25)

    console = Console()

    with Progress(
        TextColumn("{task.fields[track].title}"),
        BarColumn(bar_width=None),
        console=console,
        transient=True,
        auto_refresh=True,
    ) as progress:

        def handleTrackDownload(track: Track):
            total = randint(10, 30)

            task = progress.add_task(
                description=track.title, total=total, track=track, start=True
            )

            # simulate track download

            for _ in range(total):
                sleep(0.1)
                progress.advance(task, 1)

            console.log(track.title)
            progress.update(task, visible=False)

        with ThreadPoolExecutor(max_workers=WORKERS_COUNT) as pool:
            for item in playlist_items.items:
                track = item.item

                if isinstance(
                    track, PlaylistItems.PlaylistTrackItem.PlaylistTrack
                ):
                    pool.submit(handleTrackDownload, track=track)
