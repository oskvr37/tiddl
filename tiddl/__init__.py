import argparse
from .api import TidalApi
from .auth import getDeviceAuth, getToken


def main():
    parser = argparse.ArgumentParser(description="TIDDL, the Tidal Downloader")
    print("✅ TIDDL installed!")

    auth = getDeviceAuth()
    print(f"Go to https://{auth['verificationUriComplete']} and add device!")
    input("Hit enter when you are ready")
    token = getToken(auth["deviceCode"])
    print(token)


if __name__ == "__main__":
    main()
