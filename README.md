# Tidal Downloader

![PyPI - Downloads](https://img.shields.io/pypi/dm/tiddl?style=for-the-badge&color=%2332af64)
![PyPI - Version](https://img.shields.io/pypi/v/tiddl?style=for-the-badge)
![GitHub commits since latest release](https://img.shields.io/github/commits-since/oskvr37/tiddl/latest?style=for-the-badge)
[<img src="https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg?style=for-the-badge" />](https://gitmoji.dev)

TIDDL is Python CLI application that allows downloading Tidal tracks.

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

  TIDDL - Download Tidal tracks ✨

Options:
  -v, --verbose  Show debug logs
  --help         Show this message and exit.

Commands:
	...
```

# Basic usage

## Login with Tidal account

```bash
tiddl auth login
```

## Download resource

You can download track / album / artist / playlist / (video coming soon)
<!-- TODO: remove coming soon after adding video download -->

```bash
tiddl url https://listen.tidal.com/track/103805726 download
tiddl url https://listen.tidal.com/album/103805723 download
tiddl url https://listen.tidal.com/artist/25022 download
tiddl url https://listen.tidal.com/playlist/84974059-76af-406a-aede-ece2b78fa372 download
```

> [!TIP]
> You don't have to paste full urls, track/103805726, album/103805723 etc. will also work

## Download options

```bash
tiddl ... download -q master -o "{artist}/{title} ({album})"
```

This command will:
- download with highest quality (master)
- save track with title and album name in artist folder

### Download quality

| Quality | File extension | Details |
|:-:|:-:|:-:|
| LOW | .m4a | 96 kbps |
| NORMAL | .m4a | 320 kbps |
| HIGH | .flac | 16-bit, 44.1 kHz |
| MASTER | .flac | Up to 24-bit, 192 kHz |

### Output format

More about file templating [on wiki](https://github.com/oskvr37/tiddl/wiki/Template-formatting).

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
