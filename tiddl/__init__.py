import argparse
from .api import TidalApi


def main():
    parser = argparse.ArgumentParser(description="TIDDL, the Tidal Downloader")
    print("✅ TIDDL installed!")

    api = TidalApi()
    auth = api.getDeviceAuth()
    print(f"Go to https://{auth['verificationUriComplete']} and add device!")
    input("Hit enter when you are ready")
    token = api.getToken(auth["deviceCode"])
    print(token)


if __name__ == "__main__":
    main()
