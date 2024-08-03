import os
import time
import logging
from random import randint

from .api import TidalApi
from .auth import getDeviceAuth, getToken, refreshToken
from .config import Config
from .download import downloadTrackStream
from .parser import QUALITY_ARGS, parser
from .types import TRACK_QUALITY, TrackQuality, Track
from .utils import (
    RESOURCE,
    parseURL,
    formatFilename,
    sanitizeDirName,
    loadingSymbol,
    setMetadata,
)


def main():
    logger = logging.getLogger("TIDDL")
    stream_handler = logging.StreamHandler()
    level_name_log = ""
    function_log = ""

    args = parser.parse_args()

    if args.silent:
        log_level = logging.WARNING
    elif args.verbose:
        log_level = logging.DEBUG
        level_name_log = "\033[1;34m%(levelname)s "
        function_log = " %(funcName)s"
    else:
        log_level = logging.INFO

    stream_handler.setLevel(log_level)

    if args.no_color:
        stream_handler.setFormatter(
            logging.Formatter(f"[ %(levelname)s ] %(name)s{function_log} - %(message)s")
        )
    else:
        stream_handler.setFormatter(
            logging.Formatter(
                f"{level_name_log}\033[1;95m%(name)s\033[0;35m{function_log}\033[0m %(message)s"
            )
        )

    file_handler = logging.FileHandler("tiddl.log", "a", "utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s\t%(name)s.%(funcName)s %(message)s",
            datefmt="%x %X",
        )
    )

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler, stream_handler],
    )

    logger.debug(args)

    config = Config()

    download_path = args.download_path or config["settings"]["download_path"]
    track_quality = (
        QUALITY_ARGS[args.quality]
        if args.quality
        else config["settings"]["track_quality"]
    )
    file_template = args.file_template or config["settings"]["file_template"]

    if args.save_options:
        logger.info("saving new settings...")
        settings = config.update(
            {
                "settings": {
                    "download_path": download_path,
                    "track_quality": track_quality,
                    "file_template": file_template,
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

    def downloadTrack(track: Track, skip_existing=True, sleep=False):
        file_name = formatFilename(file_template, track)
        full_path = sanitizeDirName(f"{download_path}/{file_name}")

        # it will stop detecting existing file for other extensions
        # TODO: create better existing file detecting ✨
        if skip_existing and os.path.isfile(full_path + ".flac"):
            logger.info(f"already exists: {full_path}")
            return

        if sleep:
            sleep_time = randint(15, 25) / 10 + 1
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
            full_path,
            stream["manifest"],
            stream["manifestMimeType"],
        )

        logger.info(f"track saved in {track_path}")

        try:
            setMetadata(track_path, track)
        except Exception as e:
            logger.error(e)

    def downloadAlbum(album_id: str | int, skip_existing: bool):
        # i dont know if limit 100 is suspicious
        # but i will leave it here
        album = api.getAlbumItems(album_id, limit=100)
        for item in album["items"]:
            track = item["item"]
            downloadTrack(track, skip_existing, sleep=True)

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
                downloadTrack(track, skip_existing)
                continue

            case "album":
                downloadAlbum(input_id, skip_existing)
                continue

            case "artist":
                # TODO: include artist EPs and singles option ✨
                artist_albums = api.getArtistAlbums(input_id)

                for album in artist_albums["items"]:
                    downloadAlbum(album["id"], skip_existing)

                continue

            case "playlist":
                # TODO: add option to limit and set offset of playlist ✨
                playlist = api.getPlaylistItems(input_id)
                for item in playlist["items"]:
                    downloadTrack(item["item"], skip_existing, sleep=True)

                continue

            case _:
                logger.warning(f"invalid input: `{input_type}`")

        failed_input.append(input_id)

    if len(failed_input) > 0:
        logger.info(f"failed: {failed_input}")


if __name__ == "__main__":
    main()
