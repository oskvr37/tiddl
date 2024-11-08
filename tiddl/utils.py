import re
import os
import json
import logging
import subprocess

from datetime import datetime
from typing import TypedDict, Literal, List, get_args
from mutagen.flac import FLAC as MutagenFLAC, Picture
from mutagen.easymp4 import EasyMP4 as MutagenMP4

from .types.track import Track
from .config import HOME_DIRECTORY

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


def formatFilename(template: str, track: Track, playlist=""):
    artists = [artist["name"].strip() for artist in track["artists"]]

    release_date = datetime.strptime(
        track["streamStartDate"], "%Y-%m-%dT00:00:00.000+0000"
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


def loadingSymbol(i: int, text: str):
    symbols = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    symbol = symbols[i % len(symbols)]
    print(f"\r{text} {symbol}", end="\r")


def setMetadata(file_path: str, track: Track, cover_data=b""):
    _, extension = os.path.splitext(file_path)

    if extension == ".flac":
        metadata = MutagenFLAC(file_path)
        if cover_data:
            picture = Picture()
            picture.data = cover_data
            picture.mime = "image/jpeg"
            metadata.add_picture(picture)
    elif extension == ".m4a":
        metadata = MutagenMP4(file_path)
        # i dont know if there is a way to add cover for m4a file
    else:
        raise ValueError(f"Unknown file extension: {extension}")

    new_metadata: dict[str, str] = {
        "title": track["title"],
        "trackNumber": str(track["trackNumber"]),
        "discnumber": str(track["volumeNumber"]),
        "copyright": track["copyright"],
        "artist": track["artist"]["name"],
        "album": track["album"]["title"],
        "date": track["streamStartDate"][:10],
        # "tags": track["audioQuality"],
        # "id": str(track["id"]),
        # "url": track["url"],
    }

    try:
        metadata.update(new_metadata)
    except Exception as e:
        logger.error(e)
        return

    metadata.save()


def convertToFlac(source_path: str, file_extension: str, remove_source=True):
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


class Colors:
    def __init__(self, colored=True) -> None:
        if colored:
            self.BLACK = "\033[0;30m"
            self.GRAY = "\033[1;30m"

            self.RED = "\033[0;31m"
            self.LIGHT_RED = "\033[1;31m"

            self.GREEN = "\033[0;32m"
            self.LIGHT_GREEN = "\033[1;32m"

            self.YELLOW = "\033[0;33m"
            self.LIGHT_YELLOW = "\033[1;33m"

            self.BLUE = "\033[0;34m"
            self.LIGHT_BLUE = "\033[1;34m"

            self.PURPLE = "\033[0;35m"
            self.LIGHT_PURPLE = "\033[1;35m"

            self.CYAN = "\033[0;36m"
            self.LIGHT_CYAN = "\033[1;36m"

            self.LIGHT_GRAY = "\033[0;37m"
            self.LIGHT_WHITE = "\033[1;37m"

            self.RESET = "\033[0m"
            self.BOLD = "\033[1m"
            self.FAINT = "\033[2m"
            self.ITALIC = "\033[3m"
            self.UNDERLINE = "\033[4m"
            self.BLINK = "\033[5m"
            self.NEGATIVE = "\033[7m"
            self.CROSSED = "\033[9m"
        else:
            self.BLACK = ""
            self.GRAY = ""

            self.RED = ""
            self.LIGHT_RED = ""

            self.GREEN = ""
            self.LIGHT_GREEN = ""

            self.YELLOW = ""
            self.LIGHT_YELLOW = ""

            self.BLUE = ""
            self.LIGHT_BLUE = ""

            self.PURPLE = ""
            self.LIGHT_PURPLE = ""

            self.CYAN = ""
            self.LIGHT_CYAN = ""

            self.LIGHT_GRAY = ""
            self.LIGHT_WHITE = ""

            self.RESET = ""
            self.BOLD = ""
            self.FAINT = ""
            self.ITALIC = ""
            self.UNDERLINE = ""
            self.BLINK = ""
            self.NEGATIVE = ""
            self.CROSSED = ""


def initLogging(
    silent: bool, verbose: bool, directory=HOME_DIRECTORY, colored_logging=True
):
    c = Colors(colored_logging)

    class StreamFormatter(logging.Formatter):
        FORMATS = {
            logging.DEBUG: f"{c.BLUE}[ %(name)s ] {c.CYAN}%(funcName)s {c.RESET}%(message)s",
            logging.INFO: f"{c.GREEN}[ %(name)s ] {c.RESET}%(message)s",
            logging.WARNING: f"{c.YELLOW}[ %(name)s ] {c.RESET}%(message)s",
            logging.ERROR: f"{c.RED}[ %(name)s ] %(message)s",
            logging.CRITICAL: f"{c.RED}[ %(name)s ] %(message)s",
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record) + c.RESET

    stream_handler = logging.StreamHandler()

    file_handler = logging.FileHandler(f"{directory}/tiddl.log", "a", "utf-8")

    if silent:
        log_level = logging.WARNING
    elif verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(StreamFormatter())

    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s\t%(name)s.%(funcName)s %(message)s",
            datefmt="%x %X",
        )
    )

    # suppress logs from third-party libraries
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler, stream_handler],
    )
