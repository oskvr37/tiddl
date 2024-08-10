import re
import os
import logging
import subprocess

from typing import TypedDict, Literal, List, get_args
from mutagen.flac import FLAC as MutagenFLAC, Picture
from mutagen.easymp4 import EasyMP4 as MutagenMP4

from .types.track import Track

RESOURCE = Literal["track", "album", "artist", "playlist"]
RESOURCE_LIST: List[RESOURCE] = list(get_args(RESOURCE))


logger = logging.getLogger("utils")


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
    artist: str
    album: str
    artists: str
    playlist: str


def formatFilename(template: str, track: Track, playlist=""):
    artists = [artist["name"] for artist in track["artists"]]
    formatted_track: FormattedTrack = {
        "album": track["album"]["title"].strip(),
        "artist": track["artist"]["name"].strip(),
        "artists": ", ".join(artists).strip(),
        "id": str(track["id"]).strip(),
        "title": track["title"].strip(),
        "number": str(track["trackNumber"]).strip(),
        "playlist": playlist.strip(),
    }

    dirs = template.split("/")
    filename = dirs.pop().format(**formatted_track)

    template_without_filename = "/".join(dirs)
    formatted_dir = template_without_filename.format(**formatted_track)

    sanitized_dir = sanitizeDirName(formatted_dir)

    return sanitized_dir, filename


def sanitizeDirName(dir_name: str):
    # replace invalid characters with an underscore
    sanitized_dir = re.sub(r'[<>:"|?*]', "_", dir_name)
    # strip whitespace
    sanitized_dir = sanitized_dir.strip()

    return sanitized_dir


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


def convertToFlac(source_path: str, remove_source=True):
    source_dir, source_extension = os.path.splitext(source_path)
    dest_path = f"{source_dir}.flac"

    logger.debug((source_path, source_dir, source_extension, dest_path))

    if source_extension != ".m4a":
        return source_path

    logger.debug(f"converting `{source_path}` to FLAC")
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


def initLogging(silent: bool, verbose: bool, directory: str, colored_logging=True):
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
