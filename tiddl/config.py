import json
from typing import TypedDict, Any


class Settings(TypedDict, total=False):
    download_path: str


class ConfigData(TypedDict, total=False):
    token: str
    refresh_token: str
    token_expires_at: int
    settings: Settings


FILENAME = ".tiddl.json"
DEFAULT_CONFIG: ConfigData = {
    "token": "",
    "refresh_token": "",
    "token_expires_at": 0,
    "settings": {"download_path": "tiddl"},
}


class Config:
    def __init__(self) -> None:
        self._config: ConfigData = DEFAULT_CONFIG

        try:
            with open(FILENAME, "r") as f:
                loaded_config = json.load(f)
                self._config.update(loaded_config)
        except FileNotFoundError:
            self._save()  # save default config if file does not exist

    def _save(self) -> None:
        with open(FILENAME, "w") as f:
            json.dump(self._config, f, indent=2)

    def __getitem__(self, key: str) -> Any:
        return self._config[key]

    def __iter__(self):
        return iter(self._config)

    def __str__(self) -> str:
        return json.dumps(self._config, indent=2)

    def update(self, data: ConfigData) -> ConfigData:
        self._config.update(data)
        self._save()
        return self._config.copy()
