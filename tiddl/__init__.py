import argparse

from .api import TidalApi
from .auth import getDeviceAuth, getToken
from .config import Config


def main():
    parser = argparse.ArgumentParser(description="TIDDL, the Tidal Downloader")
    print("✅ TIDDL installed!")

    config = Config()

    if not config["token"]:
        auth = getDeviceAuth()
        print(f"Go to https://{auth['verificationUriComplete']} and add device!")
        input("Hit enter when you are ready")
        token = getToken(auth["deviceCode"])
        print(token)
        config.update({"token": token["access_token"], "refresh_token": token["refresh_token"]})
    else:
        print(config)


if __name__ == "__main__":
    main()
