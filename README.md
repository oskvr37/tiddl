# Tidal Downloader

![PyPI - Downloads](https://img.shields.io/pypi/dm/tiddl?style=for-the-badge&color=%2332af64)
![PyPI - Version](https://img.shields.io/pypi/v/tiddl?style=for-the-badge)
![GitHub commits since latest release](https://img.shields.io/github/commits-since/oskvr37/tiddl/latest?style=for-the-badge)
[<img src="https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg?style=for-the-badge" />](https://gitmoji.dev)

TIDDL is the Python CLI application that allows downloading Tidal tracks and videos!

<img src="https://raw.githubusercontent.com/oskvr37/tiddl/refs/heads/main/docs/demo.gif" alt="tiddl album download in 6 seconds" />

It's inspired by [Tidal-Media-Downloader](https://github.com/yaronzz/Tidal-Media-Downloader) - currently not mantained project.
This repository will contain features requests from that project and will be the enhanced version.

> [!WARNING]
> This app is for personal use only and is not affiliated with Tidal. Users must ensure their use complies with Tidal's terms of service and local copyright laws. Downloaded tracks are for personal use and may not be shared or redistributed. The developer assumes no responsibility for misuse of this app.

# Installation

Install package using `pip`

```bash
pip install tiddl
```

Run the package cli with `tiddl`

```bash
$ tiddl
Usage: tiddl [OPTIONS] COMMAND [ARGS]...

  TIDDL - Tidal Downloader ♫

Options:
  -v, --verbose    Show debug logs.
  -q, --quiet      Suppress logs.
  -nc, --no-cache  Omit Tidal API requests caching.
  --help           Show this message and exit.

Commands:
  auth    Manage Tidal token.
  config  Print path to the configuration file.
  fav     Get your Tidal favorites.
  file    Parse txt or JSON file with urls.
  search  Search on Tidal.
  url     Get Tidal URL.
```
## Dockerised Version (no Python required)
Based on python:alpine, slim build
**Docker run example (quickest / easiest)**
```
docker run -rm -v /downloads/dir:/root/Music/Tiddl/ -v ./config/tiddl/:/root/ >
```

**docker-compose.yml example (not required, though allows for advanced configs)**
```
services:
  tiddl:
    container_name: tiddl
    image: <ghcr.ioURL>:latest
    volumes:
      - /downloads/dir:/root/Music/Tiddl/ #default dir
      - ./config/tiddl/:/root/ # Default location of config file 
    command: tail -f /dev/null # Keep it running in background
```
**Access the container:**
```
docker exec -it tiddl sh
```

_all other instructions match python version_

# Basic usage

## Login with Tidal account

```bash
tiddl auth login
```

## Download resource

You can download track / video / album / artist / playlist

```bash
tiddl url https://listen.tidal.com/track/103805726 download
tiddl url https://listen.tidal.com/video/25747442 download
tiddl url https://listen.tidal.com/album/103805723 download
tiddl url https://listen.tidal.com/artist/25022 download
tiddl url https://listen.tidal.com/playlist/84974059-76af-406a-aede-ece2b78fa372 download
```

> [!TIP]
> You don't have to paste full urls, track/103805726, album/103805723 etc. will also work

## Download options

```bash
tiddl url track/103805726 download -q master -o "{artist}/{title} ({album})"
```

This command will:

- download with highest quality (master)
- save track with title and album name in artist folder

### Download quality

| Quality | File extension |        Details        |
| :-----: | :------------: | :-------------------: |
|   LOW   |      .m4a      |        96 kbps        |
| NORMAL  |      .m4a      |       320 kbps        |
|  HIGH   |     .flac      |   16-bit, 44.1 kHz    |
| MASTER  |     .flac      | Up to 24-bit, 192 kHz |

### Output format

More about file templating [on wiki](https://github.com/oskvr37/tiddl/wiki/Template-formatting).

## Custom tiddl home path

You can set `TIDDL_PATH` environment variable to use custom home path for tiddl.

Example CLI usage:

```sh
TIDDL_PATH=~/custom/tiddl tiddl auth login
```

# Development

Clone the repository

```bash
git clone https://github.com/oskvr37/tiddl
```

Install package with `--editable` flag

```bash
pip install -e .
```

Run tests

```bash
python -m unittest
```

# Resources

[Tidal API wiki](https://github.com/Fokka-Engineering/TIDAL)
