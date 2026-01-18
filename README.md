# Tidal Downloader

Download tracks and videos from Tidal with max quality! `tiddl` is CLI app written in Python.

> [!WARNING]
> `This app is for personal use only and is not affiliated with Tidal. Users must ensure their use complies with Tidal's terms of service and local copyright laws. Downloaded tracks are for personal use and may not be shared or redistributed. The developer assumes no responsibility for misuse of this app.`

![PyPI - Downloads](https://img.shields.io/pypi/dm/tiddl?style=for-the-badge&color=%2332af64)
![PyPI - Version](https://img.shields.io/pypi/v/tiddl?style=for-the-badge)
[<img src="https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg?style=for-the-badge" />](https://gitmoji.dev)

# Installation

`tiddl` is available at [python package index](https://pypi.org/project/tiddl/) and you can install it with your favorite Python package manager.

> [!IMPORTANT]
> Also make sure you have installed  [`ffmpeg`](https://ffmpeg.org/download.html) - it is used to convert downloaded tracks to proper format.

## uv

We recommend using [uv](https://docs.astral.sh/uv/)

```bash
uv tool install tiddl
```

## pip

You can also use [pip](https://packaging.python.org/en/latest/tutorials/installing-packages/)

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

### Error Handling

By default, tiddl stops when encountering unavailable items in collections such as playlists, albums, artists, or mixes (e.g., removed or region-locked tracks).

Use `--skip-errors` to automatically skip these items and continue downloading:

```bash
tiddl download url <url> --skip-errors
```

Skipped items are logged with track/album name and IDs for reference.

### Quality

| Quality | File extension |        Details        |
| :-----: | :------------: | :-------------------: |
|   LOW   |      .m4a      |        96 kbps        |
| NORMAL  |      .m4a      |       320 kbps        |
|  HIGH   |     .flac      |   16-bit, 44.1 kHz    |
|   MAX   |     .flac      | Up to 24-bit, 192 kHz |

### Output

You can format filenames of your downloaded resources and put them in different directories.

For example, setting output flag to `"{album.artist}/{album.title}/{item.number:02d}. {item.title}"`
will download tracks like following:

```
Music
└── Kanye West
    └── Graduation
        ├── 01. Good Morning.flac
        ├── 02. Champion.flac
        ├── 03. Stronger.flac
        ├── 04. I Wonder.flac
        ├── 05. Good Life.flac
        ├── 06. Can't Tell Me Nothing.flac
        ├── 07. Barry Bonds.flac
        ├── 08. Drunk and Hot Girls.flac
        ├── 09. Flashing Lights.flac
        ├── 10. Everything I Am.flac
        ├── 11. The Glory.flac
        ├── 12. Homecoming.flac
        ├── 13. Big Brother.flac
        └── 14. Good Night.flac
```

> [!NOTE]
> Learn more about [file templating](/docs/templating.md)

## Configuration files

Files of the app are created in your home directory. By default, the app is located at `~/.tiddl`.

You can (and should) create the `config.toml` file to configure the app how you want.

You can copy example config from docs [config.example.toml](/docs/config.example.toml)

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
cd tiddl
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
