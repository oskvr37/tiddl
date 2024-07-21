import json
from typing import TypedDict


class Settings(TypedDict):
    download_path: str


class ConfigData(TypedDict):
    token: str
    settings: Settings


FILENAME = ".tiddl.json"
DEFAULT_CONFIG: ConfigData = {"token": "", "settings": {"download_path": "tiddl"}}


class Config:
    def __init__(self) -> None:
        self.config: ConfigData = DEFAULT_CONFIG

        # load config from file or create new
        try:
            with open(FILENAME, "r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.save()

    def save(self):
        with open(FILENAME, "w") as f:
            json.dump(self.config, f)
