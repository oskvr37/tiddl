# Tidal Downloader

TIDDL is the Python CLI application that allows downloading Tidal tracks and videos!

![PyPI - Downloads](https://img.shields.io/pypi/dm/tiddl?style=for-the-badge&color=%2332af64)
![PyPI - Version](https://img.shields.io/pypi/v/tiddl?style=for-the-badge)
[<img src="https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg?style=for-the-badge" />](https://gitmoji.dev)

> [!WARNING]
> This app is for personal use only and is not affiliated with Tidal. Users must ensure their use complies with Tidal's terms of service and local copyright laws. Downloaded tracks are for personal use and may not be shared or redistributed. The developer assumes no responsibility for misuse of this app.

# Installation

`tiddl` is available at [python package index](https://pypi.org/project/tiddl/)

> [!NOTE]
> Also make sure you have installed `ffmpeg`, it is used to convert downloaded tracks to proper format.

You can install `tiddl` using your favorite python package manager.

## uv

We recommend using [uv](https://docs.astral.sh/uv/).

```bash
uv tool install tiddl
```

## pip

You can also use [pip](https://packaging.python.org/en/latest/tutorials/installing-packages/).

```bash
pip install tiddl
```

## docker

**coming soon**

# Usage

Run the app with `tiddl`

```bash
$ tiddl
 Usage: tiddl [OPTIONS] COMMAND [ARGS]...

 tiddl - download tidal tracks ♫

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --omit-cache            --no-omit-cache      [default: no-omit-cache]                                       │
│ --debug                 --no-debug           [default: no-debug]                                            │
│ --install-completion                         Install completion for the current shell.                      │
│ --show-completion                            Show completion for the current shell, to copy it or customize │
│                                              the installation.                                              │
│ --help                                       Show this message and exit.                                    │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────╮
│ auth       Manage Tidal authentication.                                                                     │
│ download   Download Tidal resources.                                                                        │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Authentication

Login to app with your Tidal account: run the command below and follow instructions.

```bash
tiddl auth login
```

## Downloading

You can download tracks / videos / albums / artists / playlists / mixes.

```bash
$ tiddl download url <url>
```

> [!TIP]
> You don't have to paste full urls, track/103805726, album/103805723 etc. will also work

Run `tiddl download` to see available download options.

### Quality

| Quality | File extension |        Details        |
| :-----: | :------------: | :-------------------: |
|   LOW   |      .m4a      |        96 kbps        |
| NORMAL  |      .m4a      |       320 kbps        |
|  HIGH   |     .flac      |   16-bit, 44.1 kHz    |
|   MAX   |     .flac      | Up to 24-bit, 192 kHz |

### Templating

More about file templating [on wiki](https://github.com/oskvr37/tiddl/wiki/Template-formatting).

## Environment variables

### Custom app path

You can set `TIDDL_PATH` environment variable to use custom path for `tiddl` app.

Example CLI usage:

```sh
TIDDL_PATH=~/custom/tiddl tiddl auth login
```

### Auth stopped working?

Set `TIDDL_AUTH` environment variable to use another credentials.

TIDDL_AUTH=<CLIENT_ID>;<CLIENT_SECRET>

# Development

Clone the repository

```bash
git clone https://github.com/oskvr37/tiddl
```

You should create virtual environment and activate it

```bash
uv venv
source .venv/Scripts/activate
```

Install package with `--editable` flag

```bash
uv pip install -e .
```

# Resources

[Tidal API wiki (api endpoints)](https://github.com/Fokka-Engineering/TIDAL)

[Tidal-Media-Downloader (inspiration)](https://github.com/yaronzz/Tidal-Media-Downloader)
