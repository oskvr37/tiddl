# Tidal Downloader

TIDDL is Python CLI application that allows downloading Tidal tracks.

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

# Usage

** In progress **

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
