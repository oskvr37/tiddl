# Tidal Downloader

TIDDL is the Python CLI application that allows downloading Tidal tracks.
Fully typed, only 2 requirements.

![GitHub top language](https://img.shields.io/github/languages/top/oskvr37/tiddl?style=for-the-badge)
![PyPI - Version](https://img.shields.io/pypi/v/tiddl?style=for-the-badge)
![GitHub commits since latest release](https://img.shields.io/github/commits-since/oskvr37/tiddl/latest?style=for-the-badge)
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
> go to https://link.tidal.com/xxxxx and add device!
authenticated!
token expires in 7 days
```

Use `tiddl -h` to show help message

# CLI

After authentication - when your token is ready - you can start downloading!

You can download `tracks` `albums` `playlists` `artists albums`

- `tiddl -s -q high` sets high quality as default quality
- `tiddl <input>` downloads with high quality
- `tiddl <input> -q master` downloads with best possible quality
- `tiddl 284165609 -p my_folder -o "{artist} - {title}"` downloads track to `my_folder/{artist} - {title}.flac`
- `tiddl track/284165609 -p my_folder -o "{artist} - {title}" -s` same as above, but saves `my_folder` as default download path and `{artist} - {title}` as default file format

### Valid input

- 284165609 (will treat this as track id)
- https://tidal.com/browse/track/284165609
- track/284165609
- https://listen.tidal.com/album/284165608/track/284165609
- https://listen.tidal.com/album/284165608
- album/284165608
- https://listen.tidal.com/artist/7695548
- artist/7695548
- https://listen.tidal.com/playlist/803be625-97e4-4cbb-88dd-43f0b1c61ed7
- playlist/803be625-97e4-4cbb-88dd-43f0b1c61ed7

### File formatting

| Key             | Example                   | Comment                                                       |
| --------------- | ------------------------- | ------------------------------------------------------------- |
| title           | Money Trees               |                                                               |
| artist          | Kendrick Lamar            |                                                               |
| artists         | Kendrick Lamar, Jay Rock  |                                                               |
| album           | good kid, m.A.A.d city    |                                                               |
| number          | 5                         | number on album                                               |
| disc_number     | 1                         | number of album volume                                        |
| released        | 10/22/2012                | release date                                                  |
| year            | 2012                      | year of release date                                          |
| playlist        | Kendrick Lamar Essentials | title of playlist will only appear when you download playlist |
| playlist_number | 15                        | index of track on the playlist                                |
| id              | 20556797                  | id on Tidal                                                   |

# Modules

You can also use TIDDL as module, it's fully typed so you will get type hints

```python
from tiddl import TidalApi, Config

config = Config()

api = TidalApi(
	config["token"],
	config["user"]["user_id"],
	config["user"]["country_code"]
)

album_id = 284165608

album = api.getAlbum(album_id)

print(f"{album["title"]} has {album["numberOfTracks"]} tracks!")
```

# Testing

```
python -m unittest tiddl/tests.py
```

# Resources

[Tidal API wiki](https://github.com/Fokka-Engineering/TIDAL)
