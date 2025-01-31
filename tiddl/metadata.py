import logging
import requests

from pathlib import Path

from mutagen.easymp4 import EasyMP4 as MutagenEasyMP4
from mutagen.flac import FLAC as MutagenFLAC
from mutagen.flac import Picture
from mutagen.mp4 import MP4 as MutagenMP4
from mutagen.mp4 import MP4Cover

from tiddl.models.resource import Track

logger = logging.getLogger(__name__)


def addMetadata(track_path: Path, track: Track, cover_data=b"", composer=""):
    new_metadata: dict[str, str] = {}
    extension = track_path.suffix

    if extension == ".flac":
        metadata = MutagenFLAC(track_path)
        if cover_data:
            picture = Picture()
            picture.data = cover_data
            picture.mime = "image/jpeg"
            metadata.add_picture(picture)

        if composer:
            new_metadata.update({"COMPOSER": composer})

    elif extension == ".m4a":
        if cover_data:
            metadata = MutagenMP4(track_path)
            metadata["covr"] = [
                MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)
            ]
            metadata.save(track_path)
        metadata = MutagenEasyMP4(track_path)

        if composer:
            new_metadata.update({"©wrt": composer})

    else:
        raise ValueError(f"Unknown file extension: {extension}")

    new_metadata.update(
        {
            "title": track.title,
            "tracknumber": str(track.trackNumber),
            "discnumber": str(track.volumeNumber),
            "copyright": track.copyright,
            "albumartist": track.artist.name if track.artist else "",
            "artist": ";".join(
                [artist.name.strip() for artist in track.artists]
            ),
            "album": track.album.title,
            "date": str(track.streamStartDate) if track.streamStartDate else "",
            "bpm": str(track.bpm or ""),
        }
    )

    metadata.update(new_metadata)

    try:
        metadata.save(track_path)
    except Exception as e:
        logger.error(f"Failed to add metadata to {track_path}: {e}")


class Cover:
    def __init__(self, uid: str, size=1280) -> None:
        if size > 1280:
            logger.warning(
                f"can not set cover size higher than 1280 (user set: {size})"
            )
            size = 1280

        self.uid = uid

        formatted_uid = uid.replace("-", "/")
        self.url = (
            f"https://resources.tidal.com/images/{formatted_uid}/{size}x{size}.jpg"
        )

        logger.debug((self.uid, self.url))

        self.content = self._get()

    def _get(self) -> bytes:
        req = requests.get(self.url)

        if req.status_code != 200:
            logger.error(f"could not download cover. ({req.status_code}) {self.url}")
            return b""

        logger.debug(f"got cover: {self.uid}")

        return req.content

    def save(self, directory_path: Path):
        if not self.content:
            logger.error("cover file content is empty")
            return

        file = directory_path / "cover.jpg"

        if file.exists():
            logger.debug(f"cover already exists ({file})")
            return

        try:
            with file.open("wb") as f:
                f.write(self.content)

        except FileNotFoundError as e:
            logger.error(f"could not save cover. {file} -> {e}")
