# Tidal Downloader

TIDDL is the Python CLI application that allows downloading Tidal tracks.
Fully typed, no requirements.

![GitHub top language](https://img.shields.io/github/languages/top/oskvr37/tiddl?style=for-the-badge)
![PyPI - Version](https://img.shields.io/pypi/v/tiddl?style=for-the-badge)
[<img src="https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg?style=for-the-badge" />](https://gitmoji.dev)

It's inspired by [Tidal-Media-Downloader](https://github.com/yaronzz/Tidal-Media-Downloader) - currently not mantained project.
This repository will contain features requests from that project and will be the enhanced version.

# Installation

Install package using `pip`

```bash
pip install tiddl
```

After installation you can use `tiddl` to set up auth token

```bash
$ tiddl
⚙️ Go to https://link.tidal.com/CYARD and add device!
Hit enter when you are ready...
✅ Token good for 7 days
```

Use `tiddl -h` to show help message

# Usage

After authentication - when your token is ready - you can start downloading tracks

- `tiddl -s -q high` sets high quality as default quality
- `tiddl TRACK_ID` downloads track with high quality
- `tiddl TRACK_ID -q master` downloads track with best possible quality
- `tiddl TRACK_ID -p my_folder -o my_song` downloads track to `my_folder/my_song.flac`
- `tiddl TRACK_ID -p my_folder -o my_song -s` same as above, but saves `my_folder` as default download path

You can also use TIDDL as module, it's fully typed so you will get type hints

```python
from tiddl import TidalApi, Config

config = Config()

api = TidalApi(
	config["token"],
	config["user"]["user_id"],
	config["user"]["country_code"]
)

my_playlists = api.getPlaylists()

print(f"You have got {my_playlists['totalNumberOfItems']} playlists!")
```
