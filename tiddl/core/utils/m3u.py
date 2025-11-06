from logging import getLogger
from pathlib import Path

from tiddl.core.api.models import Track

log = getLogger(__name__)


def save_tracks_to_m3u(
    tracks_with_path: list[tuple[Path, Track]], path: Path
):
    """
    tracks_with_path: [track_path, Track]
    path: m3u file location
    filename: name of the m3u file
    """

    file = path.with_suffix(".m3u")
    log.debug(f"{path=}, {file=}")

    if not tracks_with_path:
        log.warning(f"can't save '{file}', no tracks")
        return

    try:
        file.parent.mkdir(parents=True, exist_ok=True)

        with file.open("w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for track_path, track in tracks_with_path:
                f.write(
                    f"#EXTINF:{track.duration},{track.artist.name if track.artist else ''} - {track.title}\n{track_path}\n"
                )

            log.debug(f"saved m3u file as '{file}' with {len(tracks_with_path)} tracks")

    except Exception as e:
        log.error(f"can't save m3u file: {e}")
