import time
import json

from .api import TidalApi
from .auth import getDeviceAuth, getToken, refreshToken
from .config import Config
from .download import downloadTrack
from .parser import QUALITY_ARGS, parser
from .types import TRACK_QUALITY, TrackQuality


def main():
    args = parser.parse_args()
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

        print(f"✅ Saved settings to {config.config_path}")

        # TODO: pretty print settings ✨
        if settings:
            for k, v in settings.items():
                print(k, v)

    if not config["token"]:
        auth = getDeviceAuth()
        input(
            f"⚙️ Go to https://{auth['verificationUriComplete']} and add device!\nHit enter when you are ready..."
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
        print("✅ Got token!")

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
        print("✅ Refreshed token!")

    time_to_expire = config["token_expires_at"] - t_now
    days, hours = time_to_expire // (24 * 3600), time_to_expire % (24 * 3600) // 3600
    days_text = f" {days} {'day' if days == 1 else 'days'}" if days else ""
    hours_text = f" {hours} {'hour' if hours == 1 else 'hours'}" if hours else ""
    print(f"✅ Token good for{days_text}{hours_text}")

    # TODO: parse input type ✨
    # it can be track, album, playlist or artist
    track_id: str = args.input

    if not track_id:
        print("No ID nor URL provided")
        return

    api = TidalApi(
        config["token"], config["user"]["user_id"], config["user"]["country_code"]
    )

    track = api.getTrack(int(track_id), track_quality)
    quality = TRACK_QUALITY[track["audioQuality"]]

    # qualities below master dont have `bitDepth` and `sampleRate`
    # TODO: add special types for master quality 🏷️

    MASTER_QUALITIES: list[TrackQuality] = ["HI_RES_LOSSLESS", "LOSSLESS"]
    if track["audioQuality"] in MASTER_QUALITIES:
        details = f"{track['bitDepth']} bit {track['sampleRate']/1000:.1f} kHz"
    else:
        details = quality["details"]

    print(f"{quality['name']} Quality - {details}")

    file_name: str = args.file_name or track_id
    track_path = downloadTrack(
        download_path,
        file_name,
        track["manifest"],
        track["manifestMimeType"],
    )

    print(f"✨ Track saved in {track_path}")


if __name__ == "__main__":
    main()
