import json

from dataclasses import dataclass, field
from typing import TypedDict
from pathlib import Path

from tiddl.types import TrackArg


CONFIG_PATH = Path.home() / "tiddl.json"
DOWNLOAD_PATH = Path.home() / "Music" / "Tiddl"
DEFAULT_QUALITY: TrackArg = "high"


class DownloadConfig(TypedDict, total=False):
    quality: TrackArg
    path: str


class AuthConfig(TypedDict, total=False):
    token: str
    refresh_token: str
    expires: int


class ConfigFile(TypedDict, total=False):
    download: DownloadConfig
    auth: AuthConfig


DEFAULT_CONFIG: ConfigFile = {
    "download": {"quality": DEFAULT_QUALITY, "path": str(DOWNLOAD_PATH)},
    "auth": {"token": "", "refresh_token": "", "expires": 0},
}


@dataclass
class Config:
    """Configuration class for loading and updating CLI configuration file."""

    config: ConfigFile = field(default_factory=lambda: DEFAULT_CONFIG)

    def __post_init__(self):
        """Merge loaded configuration with defaults after initialization."""

        try:
            with open(CONFIG_PATH, "r") as f:
                loaded_config: ConfigFile = json.load(f)

            self.config = merge(loaded_config, self.config)

        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def update(self, new_config: ConfigFile):
        """Update the configuration with the new values and save it to the file."""

        self.config = merge(new_config, self.config)

        with open(CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=2)


def merge(source, destination):
    """
    Recursively merge two dictionaries.
    https://stackoverflow.com/a/20666342
    """

    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

    return destination
