import json
import logging
from typing import TypedDict, Any
from .types import TrackQuality


class Settings(TypedDict, total=False):
    download_path: str
    track_quality: TrackQuality


class User(TypedDict, total=False):
    user_id: str
    country_code: str


class ConfigData(TypedDict, total=False):
    token: str
    refresh_token: str
    token_expires_at: int
    settings: Settings
    user: User


DEFAULT_PATH = ".tiddl_config.json"
DEFAULT_CONFIG: ConfigData = {
    "token": "",
    "refresh_token": "",
    "token_expires_at": 0,
    "settings": {"download_path": "tidal_download", "track_quality": "HIGH"},
    "user": {"user_id": "", "country_code": ""},
}


class Config:
    def __init__(self, config_path=DEFAULT_PATH) -> None:
        self.config_path = config_path
        self._config: ConfigData = DEFAULT_CONFIG

        try:
            with open(self.config_path, "r") as f:
                logging.debug("loading from config file")
                loaded_config = json.load(f)
                self.update(loaded_config)
        except FileNotFoundError:
            logging.debug("creating new config file")
            self._save()  # save default config if file does not exist

    def _save(self) -> None:
        with open(self.config_path, "w") as f:
            json.dump(self._config, f, indent=2)
            logging.debug("saved config")

    def __getitem__(self, key: str) -> Any:
        return self._config[key]

    def __iter__(self):
        return iter(self._config)

    def __str__(self) -> str:
        return json.dumps(self._config, indent=2)

    def update(self, data: ConfigData) -> ConfigData:
        self._config.update(data)
        logging.debug("updated config")
        self._save()
        return self._config.copy()
