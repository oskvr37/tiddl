from pydantic import BaseModel
from pathlib import Path

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


class ConfigFile(BaseModel):
    download: DownloadConfig = DownloadConfig()
    auth: AuthConfig = AuthConfig()


TEMP = Path("tiddl.json")

with TEMP.open("w") as f:
    f.write(ConfigFile().model_dump_json(indent=CONFIG_INDENT))

with TEMP.open() as f:
    config = ConfigFile.model_validate_json(f.read())
