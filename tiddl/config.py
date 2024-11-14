import json
import logging

from pathlib import Path
from typing import TypedDict, Any
from .types import TrackArg


class User(TypedDict):
    user_id: str
    country_code: str


class ConfigData(TypedDict):
    token: str
    refresh_token: str
    token_expires_at: int
    user: User
    download_path: str
    track_quality: TrackArg
    track_template: str
    album_template: str
    playlist_template: str
    file_extension: str


class ConfigDataOptional(TypedDict, total=False):
    token: str
    refresh_token: str
    token_expires_at: int
    user: User
    download_path: str
    track_quality: TrackArg
    track_template: str
    album_template: str
    playlist_template: str
    file_extension: str


HOME_DIRECTORY = str(Path.home())
CONFIG_FILENAME = ".tiddl_config.json"
DEFAULT_CONFIG: ConfigData = {
    "token": "",
    "refresh_token": "",
    "token_expires_at": 0,
    "download_path": f"{HOME_DIRECTORY}/tidal_download",
    "track_quality": "normal",
    "track_template": "{artist}/{title}",
    "album_template": "{artist}/{album}/{title}",
    "playlist_template": "{playlist}/{title}",
    "file_extension": "",
    "user": {"user_id": "", "country_code": ""},
}


class Config:
    def __init__(self, config_path="") -> None:
        if config_path == "":
            self.config_directory = HOME_DIRECTORY
        else:
            self.config_directory = config_path

        self.config_path = f"{self.config_directory}/{CONFIG_FILENAME}"
        self._config: ConfigData = DEFAULT_CONFIG
        self._logger = logging.getLogger("Config")

        try:
            with open(self.config_path, "r") as f:
                loaded_config: ConfigDataOptional = json.load(f)
                loaded_settings = loaded_config.get("settings")
                self._logger.debug(f"loaded {loaded_settings}")
                self.update(loaded_config)

        except FileNotFoundError:
            self._logger.debug("creating new file")
            self._save()  # save default config if file does not exist
            self._logger.debug("created new file")

    def _save(self) -> None:
        with open(self.config_path, "w") as f:
            self._logger.debug(self._config.get("settings"))
            json.dump(self._config, f, indent=2)

    def __getitem__(self, key: str) -> Any:
        return self._config[key]

    def __iter__(self):
        return iter(self._config)

    def __str__(self) -> str:
        return json.dumps(self._config, indent=2)

    def update(self, data: ConfigDataOptional) -> ConfigData:
        self._logger.debug("updating")
        self._config.update(data)
        self._save()
        self._logger.debug("updated")
        return self._config.copy()
