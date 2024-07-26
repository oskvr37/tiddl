import argparse
import time

from .api import TidalApi
from .auth import getDeviceAuth, getToken, refreshToken
from .config import Config
from .download import downloadTrack


def main():
    parser = argparse.ArgumentParser(description="TIDDL, the Tidal Downloader")
    config = Config()

    if not config["token"]:
        auth = getDeviceAuth()
        input(
            f"⚙️ Go to https://{auth['verificationUriComplete']} and add device!\nHit enter when you are ready..."
        )
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
    days_text = f" {days} {"day" if days == 1 else "days"}" if days else ""
    hours_text = f" {hours} {"hour" if hours == 1 else "hours"}" if hours else ""
    print(f"✅ Token good for{days_text}{hours_text}")

    api = TidalApi(
        config["token"], config["user"]["user_id"], config["user"]["country_code"]
    )

    playlists = api.getPlaylists()
    print(f"You have got {playlists['totalNumberOfItems']} playlists.")

    track_id = int(input("Enter track id to download: "))

    track = api.getTrack(track_id, config["settings"]["track_quality"])
    track_path = downloadTrack(track_id, track["manifest"], config["settings"]["download_path"])
    print(f"✨ Track saved in {track_path}")


if __name__ == "__main__":
    main()
