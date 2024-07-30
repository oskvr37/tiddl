import os
import argparse

from .types import TRACK_QUALITY, TrackQuality


def shouldNotColor() -> bool:
    # TODO: add more checks ✨
    checks = ["NO_COLOR" in os.environ]
    return any(checks)


parser = argparse.ArgumentParser(
    description="\033[4mTIDDL\033[0m - Tidal Downloader",
    epilog="options defaults will be fetched from your config file.",
)

parser.add_argument(
    "input",
    type=str,
    nargs="?",
    const=True,
    help="track, \033[9malbum, playlist or artist\033[0m - can be \033[9mlink\033[0m or id",
)

parser.add_argument(
    "-o",
    type=str,
    nargs="?",
    const=True,
    help="output file name",
    dest="file_name",
)

parser.add_argument(
    "-p",
    type=str,
    nargs="?",
    const=True,
    help="download destination path",
    dest="download_path",
)

QUALITY_ARGS: dict[str, TrackQuality] = {
    details["arg"]: quality for quality, details in TRACK_QUALITY.items()
}

parser.add_argument(
    "-q",
    nargs="?",
    help="track quality",
    dest="quality",
    choices=QUALITY_ARGS.keys(),
)

parser.add_argument(
    "-s",
    help="save options to config // show config file",
    dest="save_options",
    action="store_true",
)

parser.add_argument(
    "--silent",
    help="silent mode",
    action="store_true",
)

parser.add_argument(
    "--verbose",
    help="show debug logs",
    action="store_true",
)

parser.add_argument(
    "--no-color",
    help="suppress output colors",
    action="store_true",
    default=shouldNotColor(),
)
