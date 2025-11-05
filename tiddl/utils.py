import re
import os
import logging

from ffmpeg_asyncio import FFmpeg
from ffmpeg_asyncio.types import Option as FFmpegOption

from pydantic import BaseModel
from urllib.parse import urlparse
from pathlib import Path

from typing import Literal, Union, get_args

from tiddl.models.constants import TrackQuality, QUALITY_TO_ARG
from tiddl.models.resource import Track, Video

ResourceTypeLiteral = Literal["track", "video", "album", "playlist", "artist", "mix"]


class TidalResource(BaseModel):
    type: ResourceTypeLiteral
    id: str

    @property
    def url(self) -> str:
        return f"https://listen.tidal.com/{self.type}/{self.id}"

    @classmethod
    def fromString(cls, string: str):
        """
        Extracts the resource type (e.g., "track", "album")
        and resource ID from a given input string.

        The input string can either be a full URL or a shorthand string
        in the format `resource_type/resource_id` (e.g., `track/12345678`).
        """

        path = urlparse(string).path
        resource_type, resource_id = path.split("/")[-2:]

        if resource_type not in get_args(ResourceTypeLiteral):
            raise ValueError(f"Invalid resource type: {resource_type}")

        digit_resource_types: list[ResourceTypeLiteral] = [
            "track",
            "album",
            "video",
            "artist",
        ]

        if resource_type in digit_resource_types and not resource_id.isdigit():
            raise ValueError(f"Invalid resource id: {resource_id}")

        return cls(type=resource_type, id=resource_id)  # type: ignore

    def __str__(self) -> str:
        return f"{self.type}/{self.id}"


def sanitizeString(string: str) -> str:
    pattern = r'[\\/:"*?<>|]+'
    return re.sub(pattern, "", string)


def formatTrack(
    template: str,
    track: Track,
    album_artist="",
    playlist_title="",
    playlist_index=0,
) -> str:
    artist = sanitizeString(track.artist.name) if track.artist else ""
    features = [
        sanitizeString(track_artist.name)
        for track_artist in track.artists
        if track_artist.name != artist
    ]

    track_dict = {
        "id": str(track.id),
        "title": sanitizeString(track.title),
        "version": sanitizeString(track.version or ""),
        "artist": artist,
        "artists": ", ".join([artist] + features),
        "features": ", ".join(features),
        "album": sanitizeString(track.album.title),
        "number": track.trackNumber,
        "disc": track.volumeNumber,
        "date": (track.streamStartDate if track.streamStartDate else ""),
        # i think we can remove year as we are able to format date
        "year": track.streamStartDate.strftime("%Y") if track.streamStartDate else "",
        "playlist": sanitizeString(playlist_title),
        "bpm": track.bpm or "",
        "quality": QUALITY_TO_ARG[track.audioQuality],
        "album_artist": sanitizeString(album_artist),
        "playlist_number": playlist_index or 0,
    }

    formatted_track = template.format(**track_dict).strip()

    disallowed_chars = r'[\\:"*?<>|]+'
    invalid_chars = re.findall(disallowed_chars, formatted_track)

    if invalid_chars:
        raise ValueError(
            f"Template '{template}' and formatted track '{formatted_track}' contains disallowed characters: {' '.join(sorted(set(invalid_chars)))}"
        )

    return formatted_track


def formatResource(
    template: str,
    resource: Union[Track, Video],
    album_artist="",
    playlist_title="",
    playlist_index=0,
) -> str:
    artist = sanitizeString(resource.artist.name) if resource.artist else ""

    features = [
        sanitizeString(item_artist.name)
        for item_artist in resource.artists
        if item_artist.name != artist
    ]

    resource_dict = {
        "id": str(resource.id),
        "title": sanitizeString(resource.title),
        "artist": artist,
        "artists": ", ".join(features + [artist]),
        "features": ", ".join(features),
        "album": sanitizeString(resource.album.title if resource.album else ""),
        "album_id": str(resource.album.id if resource.album else ""),
        "number": resource.trackNumber,
        "disc": resource.volumeNumber,
        "date": (resource.streamStartDate if resource.streamStartDate else ""),
        # i think we can remove year as we are able to format date
        "year": (
            resource.streamStartDate.strftime("%Y") if resource.streamStartDate else ""
        ),
        "playlist": sanitizeString(playlist_title),
        "album_artist": sanitizeString(album_artist),
        "playlist_number": playlist_index or 0,
        "quality": "",
        "version": "",
        "bpm": "",
    }

    if isinstance(resource, Track):
        resource_dict.update(
            {
                "version": sanitizeString(resource.version or ""),
                "quality": QUALITY_TO_ARG[resource.audioQuality],
                "bpm": resource.bpm or "",
            }
        )

    elif isinstance(resource, Video):
        resource_dict.update({"quality": resource.quality})

    formatted_template = template.format(**resource_dict).strip()

    disallowed_chars = r'[\\:"*?<>|]+'
    invalid_chars = re.findall(disallowed_chars, formatted_template)

    if invalid_chars:
        raise ValueError(
            f"Template '{template}' and formatted resource '{formatted_template}'"
            f"contains disallowed characters: {' '.join(sorted(set(invalid_chars)))}"
        )

    return formatted_template


def findTrackFilename(
    track_quality: TrackQuality, download_quality: TrackQuality, file_name: Path
) -> Path:
    """
    Predict track extension.
    """

    FLAC_QUALITIES: list[TrackQuality] = ["LOSSLESS", "HI_RES_LOSSLESS"]

    if download_quality in FLAC_QUALITIES and track_quality in FLAC_QUALITIES:
        extension = ".flac"
    else:
        extension = ".m4a"

    full_file_name = file_name.with_suffix(extension)

    return full_file_name


async def convertFileExtension(
    source_file: Path,
    extension: str,
    remove_source=False,
    is_video=False,
    copy_audio=False,
) -> Path:
    """
    Converts `source_file` extension and returns `Path` of file with new `extension`.

    Removes `source_file` when `remove_source` is truthy.
    """

    try:
        output_file = source_file.with_suffix(extension)
    except ValueError as e:
        logging.error(e)
        return source_file

    logging.debug((source_file, output_file, extension, copy_audio, is_video))

    if extension == source_file.suffix:
        logging.debug("Conversion not required, already %s", extension)
        return source_file

    ffmpeg_args: dict[str, FFmpegOption | None] = {"loglevel": "error"}

    if copy_audio:
        ffmpeg_args["acodec"] = "copy"

    if is_video:
        ffmpeg_args["vcodec"] = "copy"

    try:
        logging.debug("Trying conversion")
        ffmpeg = FFmpeg().option("y")
        ffmpeg.input(str(source_file))
        ffmpeg.output(str(output_file), ffmpeg_args)

        @ffmpeg.on("completed")
        def on_completed():
            logging.debug(f"converted {output_file}")
            if remove_source:
                try:
                    os.remove(source_file)
                except OSError as e:
                    logging.error(f"can't remove source file {source_file}: {e}")

        await ffmpeg.execute()

    except Exception as e:
        logging.error(f"can't convert file {source_file}: {e}")
        return source_file

    return output_file


def savePlaylistM3U(
    playlist_tracks: list[tuple[Path, Track]], path: Path, filename="playlist.m3u"
):
    """
    playlist_tracks: [track_path, Track]
    path: m3u file location
    filename: name of the m3u file
    """

    file = path / sanitizeString(filename)
    logging.debug(f"saving m3u file at {file}")

    if not playlist_tracks:
        logging.warning(f"playlist {file} is empty")
        return

    try:
        with file.open("w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for track_path, track in playlist_tracks:
                f.write(
                    f"#EXTINF:{track.duration},{track.artist.name if track.artist else ''} - {track.title}\n{track_path}\n"
                )

            logging.debug(
                f"saved m3u file as {file} with {len(playlist_tracks)} tracks"
            )

    except Exception as e:
        logging.error(f"can't save playlist m3u file: {e}")
