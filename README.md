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
