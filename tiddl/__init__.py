import time
import logging

from random import randint

from .api import TidalApi
from .auth import getDeviceAuth, getToken, refreshToken
from .config import Config
from .download import downloadTrackStream
from .parser import QUALITY_ARGS, parser
from .types import TRACK_QUALITY, TrackQuality
from .utils import RESOURCE, parseURL


def main():
    args = parser.parse_args()

    logger = logging.getLogger("TIDDL")
    stream_handler = logging.StreamHandler()
    function_log = ""

    if args.silent:
        log_level = logging.ERROR
    elif args.verbose:
        log_level = logging.DEBUG
        function_log = " %(funcName)s"
    else:
        log_level = logging.INFO

    stream_handler.setLevel(log_level)

    if args.no_color:
        stream_handler.setFormatter(
            logging.Formatter(
                f"[ %(levelname)s ] (%(name)s){function_log} - %(message)s"
            )
        )
    else:
        stream_handler.setFormatter(
            logging.Formatter(
                f"\033[1;34m%(levelname)s\033[0m \033[1;95m%(name)s{function_log}\033[0m %(message)s"
            )
        )

    file_handler = logging.FileHandler("tiddl.log", "w", "utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(levelname)s\t%(name)s.%(funcName)s :: %(message)s")
    )

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler, stream_handler],
    )

    config = Config()

    download_path = args.download_path or config["settings"]["download_path"]
    track_quality = (
        QUALITY_ARGS[args.quality]
        if args.quality
        else config["settings"]["track_quality"]
    )

    if args.save_options:
        settings = config.update(
            {
                "settings": {
                    "download_path": download_path,
                    "track_quality": track_quality,
                }
            }
        ).get("settings")

        logger.info(f"saved settings to {config.config_path}")

        if settings:
            print("Current Settings:")
            for k, v in settings.items():
                print(f"\t'{k.upper()}' {v}")

    if not config["token"]:
        auth = getDeviceAuth()
        input(
            f"go to https://{auth['verificationUriComplete']} and add device!\nhit enter when you are ready..."
        )

        # TODO: refresh auth status automatically ✨
        token = getToken(auth["deviceCode"])
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
    logger.info(f"token expires in{days_text}{hours_text}")

    user_input: str = args.input

    if not user_input:
        logger.warning("no ID nor URL provided")
        return

    input_type: RESOURCE
    input_id: str

    if user_input.isdigit():
        input_type = "track"
        input_id = user_input
    else:
        input_type, input_id = parseURL(user_input)

    api = TidalApi(
        config["token"], config["user"]["user_id"], config["user"]["country_code"]
    )

    def downloadTrack(track_id: str | int, file_name: str, sleep=False):
        if sleep:
            sleep_time = randint(10, 30) / 10 + 1
            logger.info(f"sleeping for {sleep_time}s")
            time.sleep(sleep_time)

        stream = api.getTrackStream(track_id, track_quality)
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
            download_path,
            file_name,
            stream["manifest"],
            stream["manifestMimeType"],
        )

        logger.info(f"track saved in {track_path}")

    def downloadAlbum(album_id: str | int):
        # i dont know if limit 100 is suspicious
        # but i will leave it here
        album = api.getAlbumItems(album_id, limit=100)

        for item in album["items"]:
            track = item["item"]
            track_id = str(track["id"])
            downloadTrack(track_id, track["title"], sleep=True)

    match input_type:
        case "track":
            downloadTrack(input_id, args.file_name or input_id)

        case "album":
            downloadAlbum(input_id)

        case "artist":
            # TODO: include artist EPs and singles option ✨
            artist_albums = api.getArtistAlbums(input_id)

            for album in artist_albums["items"]:
                downloadAlbum(album["id"])

        case "playlist":
            # TODO: add option to limit and set offset of playlist ✨
            playlist = api.getPlaylistItems(input_id)
            for item in playlist["items"]:
                downloadTrack(item["item"]["id"], item["item"]["title"], sleep=True)

        case _:
            logger.warning(f"invalid input: `{input_type}`")


if __name__ == "__main__":
    main()
