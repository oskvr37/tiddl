import re
import os
import json
import logging
import subprocess

from datetime import datetime
from typing import TypedDict, Literal, List, get_args
from mutagen.flac import FLAC as MutagenFLAC, Picture
from mutagen.easymp4 import EasyMP4 as MutagenEasyMP4
from mutagen.mp4 import MP4Cover, MP4 as MutagenMP4

from .types.track import Track

RESOURCE = Literal["track", "album", "artist", "playlist"]
RESOURCE_LIST: List[RESOURCE] = list(get_args(RESOURCE))


logger = logging.getLogger("utils")


def parseFileInput(file: str) -> list[str]:
    _, file_extension = os.path.splitext(file)
    logger.debug(file, file_extension)
    urls_set: set[str] = set()

    if file_extension == ".txt":
        with open(file) as f:
            data = f.read()
        urls_set.update(data.splitlines())
    elif file_extension == ".json":
        with open(file) as f:
            data = json.load(f)
        urls_set.update(data)
    else:
        logger.warning(f"a file with '{file_extension}' extension is not supported!")

    filtered_urls = [url for url in urls_set if type(url) == str]

    return filtered_urls


def parseURL(url: str) -> tuple[RESOURCE, str]:
    # remove trailing slash
    url = url.rstrip("/")
    # remove params
    url = url.split("?")[0]

    fragments = url.split("/")

    if len(fragments) < 2:
        raise ValueError(f"Invalid input: {url}")

    parsed_type, parsed_id = fragments[-2], fragments[-1]

    if parsed_type not in RESOURCE_LIST:
        raise ValueError(f"Invalid resource type: {parsed_type} ({url})")

    return parsed_type, parsed_id


class FormattedTrack(TypedDict):
    id: str
    title: str
    number: str
    disc_number: str
    artist: str
    album: str
    artists: str
    playlist: str
    released: str
    year: str
    playlist_number: str


def formatFilename(template: str, track: Track, playlist=""):
    artists = [artist["name"].strip() for artist in track["artists"]]

    release_date = datetime.strptime(
        track["streamStartDate"], "%Y-%m-%dT%H:%M:%S.000+0000"
    )

    formatted_track: FormattedTrack = {
        "album": re.sub(r'[<>:"|?*/\\]', "_", track["album"]["title"].strip()),
        "artist": track["artist"]["name"].strip(),
        "artists": ", ".join(artists),
        "id": str(track["id"]),
        "title": track["title"].strip(),
        "number": str(track["trackNumber"]),
        "disc_number": str(track["volumeNumber"]),
        "playlist": playlist.strip(),
        "released": release_date.strftime("%m-%d-%Y"),
        "year": release_date.strftime("%Y"),
        "playlist_number": str(track.get("playlistNumber", "")),
    }

    dirs = template.split("/")
    filename = dirs.pop()

    formatted_filename = filename.format(**formatted_track)
    formatted_dir = "/".join(dirs).format(**formatted_track)

    return sanitizeDirName(formatted_dir), sanitizeFileName(formatted_filename)


def sanitizeDirName(dir_name: str):
    # replace invalid characters with an underscore
    sanitized = re.sub(r'[<>:"|?*]', "_", dir_name)
    # strip whitespace
    sanitized = sanitized.strip()

    return sanitized


def sanitizeFileName(file_name: str):
    # replace invalid characters with an underscore
    sanitized = re.sub(r'[<>:"|?*/\\]', "_", file_name)
    # strip whitespace
    sanitized = sanitized.strip()

    return sanitized


def setMetadata(file: str, extension: str, track: Track, cover_data=b""):
    if extension == "flac":
        metadata = MutagenFLAC(file)
        if cover_data:
            picture = Picture()
            picture.data = cover_data
            picture.mime = "image/jpeg"
            metadata.add_picture(picture)
    elif extension == "m4a":
        if cover_data:
            metadata = MutagenMP4(file)
            metadata["covr"] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
            metadata.save(file)
        metadata = MutagenEasyMP4(file)
    else:
        raise ValueError(f"Unknown file extension: {extension}")

    new_metadata: dict[str, str] = {
        "title": track["title"],
        "trackNumber": str(track["trackNumber"]),
        "discnumber": str(track["volumeNumber"]),
        "copyright": track["copyright"],
        "albumartist": track["artist"]["name"],
        "artist": ";".join([artist["name"].strip() for artist in track["artists"]]),
        "album": track["album"]["title"],
        "date": track["streamStartDate"][:10],
    }

    metadata.update(new_metadata)

    try:
        metadata.save(file)
    except Exception as e:
        logger.error(f"Failed to set metadata for {extension}: {e}")


def convertFileExtension(source_path: str, file_extension: str, remove_source=True):
    source_dir, source_extension = os.path.splitext(source_path)
    dest_path = f"{source_dir}.{file_extension}"

    logger.debug((source_path, source_dir, source_extension, dest_path))

    if source_extension == f".{file_extension}":
        return source_path

    logger.debug(f"converting `{source_path}` to `{file_extension}`")
    command = ["ffmpeg", "-i", source_path, dest_path]
    result = subprocess.run(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    if result.returncode != 0:
        logger.error(result.stderr)
        return source_path

    if remove_source:
        os.remove(source_path)

    return dest_path
