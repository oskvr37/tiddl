import logging
import requests

from pathlib import Path

from mutagen.easymp4 import EasyMP4 as MutagenEasyMP4
from mutagen.flac import FLAC as MutagenFLAC
from mutagen.flac import Picture
from mutagen.mp4 import MP4 as MutagenMP4
from mutagen.mp4 import MP4Cover

from tiddl.models.resource import Track, Video
from tiddl.models.api import AlbumItemsCredits

from typing import List

logger = logging.getLogger(__name__)


def addMetadata(
    track_path: Path,
    track: Track,
    cover_data=b"",
    credits: List[AlbumItemsCredits.ItemWithCredits.CreditsEntry] = [],
    album_artist="",
):
    logger.debug((track_path, track.id))

    extension = track_path.suffix

    # TODO: handle mutagen exceptions

    if extension == ".flac":
        metadata = MutagenFLAC(track_path)
        if cover_data:
            picture = Picture()
            picture.data = cover_data
            picture.mime = "image/jpeg"
            metadata.add_picture(picture)

        metadata["TITLE"] = track.title + (track.version if track.version else "")
        metadata["WORK"] = track.title + (track.version if track.version else "")
        metadata["TRACKNUMBER"] = str(track.trackNumber)
        metadata["DISCNUMBER"] = str(track.volumeNumber)

        metadata["ALBUM"] = track.album.title

        metadata["ARTIST"] = "; ".join(
            [artist.name.strip() for artist in track.artists]
        )

        if album_artist:
            metadata["ALBUMARTIST"] = album_artist
        elif track.artist:
            metadata["ALBUMARTIST"] = track.artist.name

        if track.streamStartDate:
            metadata["DATE"] = track.streamStartDate.strftime("%Y-%m-%d")
            metadata["ORIGINALDATE"] = track.streamStartDate.strftime(
                "%Y-%m-%d"
            )
            metadata["YEAR"] = str(track.streamStartDate.strftime("%Y"))
            metadata["ORIGINALYEAR"] = str(track.streamStartDate.strftime("%Y"))

        if track.copyright:
            metadata["COPYRIGHT"] = track.copyright

        metadata["ISRC"] = track.isrc

        if track.bpm:
            metadata["BPM"] = str(track.bpm)

        for entry in credits:
            metadata[entry.type.upper()] = [
                contributor.name for contributor in entry.contributors
            ]

    elif extension == ".m4a":
        if cover_data:
            metadata = MutagenMP4(track_path)
            metadata["covr"] = [
                MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)
            ]
            metadata.save(track_path)

        metadata = MutagenEasyMP4(track_path)
        metadata.update(
            {
                "title": track.title,
                "tracknumber": str(track.trackNumber),
                "discnumber": str(track.volumeNumber),
                "copyright": track.copyright if track.copyright else "",
                "albumartist": track.artist.name if track.artist else "",
                "artist": ";".join(
                    [artist.name.strip() for artist in track.artists]
                ),
                "album": track.album.title,
                "date": str(track.streamStartDate)
                if track.streamStartDate
                else "",
                "bpm": str(track.bpm or 0),
            }
        )

    else:
        raise ValueError(f"Unknown file extension: {extension}")

    try:
        metadata.save(track_path)
    except Exception as e:
        logger.error(f"Failed to add metadata to {track_path}: {e}")


def addVideoMetadata(path: Path, video: Video):
    metadata = MutagenEasyMP4(path)

    metadata.update(
        {
            "title": video.title,
            "albumartist": video.artist.name if video.artist else "",
            "artist": ";".join(
                [artist.name.strip() for artist in video.artists]
            ),
            "album": video.album.title if video.album else "",
            "date": str(video.streamStartDate) if video.streamStartDate else "",
        }
    )

    if video.trackNumber:
        metadata["tracknumber"] = str(video.trackNumber)

    if video.volumeNumber:
        metadata["discnumber"] = str(video.volumeNumber)

    try:
        metadata.save(path)
    except Exception as e:
        logger.error(f"Failed to add metadata to {path}: {e}")


class Cover:
    # TODO: cache covers

    def __init__(self, uid: str, size=1280) -> None:
        if size > 1280:
            logger.warning(
                f"can not set cover size higher than 1280 (user set: {size})"
            )
            size = 1280

        self.uid = uid

        formatted_uid = uid.replace("-", "/")
        self.url = f"https://resources.tidal.com/images/{formatted_uid}/{size}x{size}.jpg"

        logger.debug((self.uid, self.url))

        self.content = self._get()

    def _get(self) -> bytes:
        req = requests.get(self.url)

        if req.status_code != 200:
            logger.error(
                f"could not download cover. ({req.status_code}) {self.url}"
            )
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
