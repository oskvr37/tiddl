from pydantic import BaseModel
from pathlib import Path
from typing import Self

from tiddl.models import TrackArg


CONFIG_PATH = Path.home() / "tiddl.json"
CONFIG_INDENT = 2


class DownloadConfig(BaseModel):
    quality: TrackArg = "high"
    path: Path = Path.home() / "Music" / "Tiddl"
    template: str = "{artist} - {title}"


class AuthConfig(BaseModel):
    token: str = ""
    refresh_token: str = ""
    expires: int = 0
    user_id: str = ""
    country_code: str = ""


class Config(BaseModel):
    download: DownloadConfig = DownloadConfig()
    auth: AuthConfig = AuthConfig()

    def save(self):
        with open(CONFIG_PATH, "w") as f:
            f.write(self.model_dump_json(indent=CONFIG_INDENT))

    @classmethod
    def fromFile(cls) -> Self:
        try:
            with CONFIG_PATH.open() as f:
                return Config.model_validate_json(f.read())
        except FileNotFoundError:
            return Config()
