import os
import time
import logging
from random import randint

from .api import TidalApi
from .auth import getDeviceAuth, getToken, refreshToken
from .config import Config, HOME_DIRECTORY
from .download import downloadTrackStream, downloadCover
from .parser import QUALITY_ARGS, parser
from .types import TRACK_QUALITY, TrackQuality, Track
from .utils import (
    RESOURCE,
    parseURL,
    formatFilename,
    loadingSymbol,
    setMetadata,
    convertToFlac,
)


def initLogging(silent: bool, verbose: bool, colored_logging=True):
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
    file_handler = logging.FileHandler(f"{HOME_DIRECTORY}/tiddl.log", "a", "utf-8")

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


def main():
    args = parser.parse_args()
    initLogging(args.silent, args.verbose, not args.no_color)

    logger = logging.getLogger("TIDDL")
    logger.debug(args)

    config = Config()

    include_singles = args.include_singles
    download_path = args.download_path or config["settings"]["download_path"]
    track_template = args.file_template or config["settings"]["track_template"]
    track_quality = (
        QUALITY_ARGS[args.quality]
        if args.quality
        else config["settings"]["track_quality"]
    )

    if args.save_options:
        logger.info("saving new settings...")
        settings = config.update(
            {
                "settings": {
                    "download_path": download_path,
                    "track_quality": track_quality,
                    "track_template": track_template,
                }
            }
        ).get("settings")

        if settings:
            print("Current Settings:")
            for k, v in settings.items():
                print(f'> {k.upper()} "{v}"')

        logger.info(f"saved settings to {config.config_path}")

    if not config["token"]:
        auth = getDeviceAuth()
        text = f"> go to https://{auth['verificationUriComplete']} and add device!"
        expires_at = time.time() + auth["expiresIn"]
        i = 0
        while time.time() < expires_at:
            for _ in range(50):
                loadingSymbol(i, text)
                i += 1
                time.sleep(0.1)
            token = getToken(auth["deviceCode"])

            if token.get("error"):
                continue

            print()

            config.update(
                {
                    "token": token["access_token"],
                    "refresh_token": token["refresh_token"],
                    "token_expires_at": int(time.time()) + token["expires_in"],
                    "user": {
                        "user_id": str(token["user"]["userId"]),
                        "country_code": token["user"]["countryCode"],
                    },
                }
            )
            logger.info(f"authenticated!")
            break
        else:
            logger.info("time for authentication has expired")
            return

    t_now = int(time.time())
    token_expired = t_now > config["token_expires_at"]

    if token_expired:
        token = refreshToken(config["refresh_token"])
        config.update(
            {
                "token": token["access_token"],
                "token_expires_at": int(time.time()) + token["expires_in"],
            }
        )
        logger.info(f"refreshed token!")

    time_to_expire = config["token_expires_at"] - t_now
    days, hours = time_to_expire // (24 * 3600), time_to_expire % (24 * 3600) // 3600
    days_text = f" {days} {'day' if days == 1 else 'days'}" if days else ""
    hours_text = f" {hours} {'hour' if hours == 1 else 'hours'}" if hours else ""
    logger.debug(f"token expires in{days_text}{hours_text}")

    user_inputs: list[str] = args.input

    if len(user_inputs) == 0:
        logger.warning("no ID nor URL provided")
        return

    api = TidalApi(
        config["token"], config["user"]["user_id"], config["user"]["country_code"]
    )

    def downloadTrack(
        track: Track, file_template: str, skip_existing=True, sleep=False, playlist=""
    ) -> tuple[str, str]:
        file_dir, file_name = formatFilename(file_template, track, playlist)

        # it will stop detecting existing file for other extensions.
        # we need to store track `id + quality` in metadata to differentiate tracks
        # TODO: create better existing file detecting ✨
        file_path = f"{download_path}/{file_dir}/{file_name}"
        if skip_existing and (
            os.path.isfile(file_path + ".m4a") or os.path.isfile(file_path + ".flac")
        ):
            logger.info(f"already exists: {file_path}")
            return file_dir, file_name

        if sleep:
            sleep_time = randint(5, 15) / 10 + 1
            logger.info(f"sleeping for {sleep_time}s")
            time.sleep(sleep_time)

        stream = api.getTrackStream(track["id"], track_quality)
        quality = TRACK_QUALITY[stream["audioQuality"]]

        MASTER_QUALITIES: list[TrackQuality] = ["HI_RES_LOSSLESS", "LOSSLESS"]
        if stream["audioQuality"] in MASTER_QUALITIES:
            bit_depth, sample_rate = stream.get("bitDepth"), stream.get("sampleRate")
            if bit_depth is None or sample_rate is None:
                raise ValueError(
                    "bitDepth and sampleRate must be provided for master qualities"
                )
            details = f"{bit_depth} bit {sample_rate/1000:.1f} kHz"
        else:
            details = quality["details"]

        logger.info(f"{file_name} :: {quality['name']} Quality - {details}")

        track_path = downloadTrackStream(
            f"{download_path}/{file_dir}",
            file_name,
            stream["manifest"],
            stream["manifestMimeType"],
        )

        setMetadata(track_path, track)

        track_path = convertToFlac(track_path)

        logger.info(f"track saved as {track_path}")

        return file_dir, file_name

    def downloadAlbum(album_id: str | int, skip_existing: bool):
        album = api.getAlbum(album_id)
        logger.info(f"album: {album['title']}")

        # i dont know if limit 100 is suspicious
        # but i will leave it here
        album_items = api.getAlbumItems(album_id, limit=100)
        file_dir = ""

        for item in album_items["items"]:
            track = item["item"]
            file_dir, file_name = downloadTrack(
                track,
                file_template=config["settings"]["album_template"],
                skip_existing=skip_existing,
                sleep=True,
            )

        if file_dir:
            downloadCover(album["cover"], f"{download_path}/{file_dir}")

    skip_existing = not args.no_skip
    failed_input = []

    for user_input in user_inputs:
        input_type: RESOURCE
        input_id: str

        if user_input.isdigit():
            input_type = "track"
            input_id = user_input
        else:
            try:
                input_type, input_id = parseURL(user_input)
            except ValueError as e:
                logger.error(e)
                failed_input.append(user_input)
                continue

        match input_type:
            case "track":
                track = api.getTrack(input_id)
                downloadTrack(
                    track, file_template=track_template, skip_existing=skip_existing
                )
                continue

            case "album":
                downloadAlbum(input_id, skip_existing)
                continue

            case "artist":
                all_albums = []
                artist_albums = api.getArtistAlbums(input_id)
                all_albums.extend(artist_albums["items"])

                if include_singles:
                    artist_singles = api.getArtistAlbums(input_id, onlyNonAlbum=True)
                    all_albums.extend(artist_singles["items"])

                for album in all_albums:
                    downloadAlbum(album["id"], skip_existing)

                continue

            case "playlist":
                # TODO: add option to limit and set offset of playlist ✨
                playlist = api.getPlaylist(input_id)
                logger.info(f"playlist: {playlist['title']} ({playlist['url']})")

                playlist_items = api.getPlaylistItems(input_id)
                for item in playlist_items["items"]:
                    downloadTrack(
                        item["item"],
                        file_template=config["settings"]["playlist_template"],
                        skip_existing=skip_existing,
                        sleep=True,
                        playlist=playlist["title"],
                    )

                continue

            case _:
                logger.warning(f"invalid input: `{input_type}`")

        failed_input.append(input_id)

    if len(failed_input) > 0:
        logger.info(f"failed: {failed_input}")


if __name__ == "__main__":
    main()
