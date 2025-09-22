from os import environ, makedirs
from pydantic import BaseModel
from pathlib import Path

from tiddl.models.constants import TrackArg, SinglesFilter

TIDDL_ENV_KEY = "TIDDL_PATH"

# 3.0 TODO: rename HOME_PATH to TIDDL_PATH
# 3.0 TODO: add /tiddl to Path.home()
HOME_PATH = Path(environ[TIDDL_ENV_KEY]) if environ.get(TIDDL_ENV_KEY) else Path.home()

makedirs(HOME_PATH, exist_ok=True)

CONFIG_PATH = HOME_PATH / "tiddl.json"
CONFIG_INDENT = 2


class TemplateConfig(BaseModel):
    track: str = "{artist} - {title}"
    video: str = "{artist} - {title}"
    album: str = "{album_artist}/{album}/{number:02d}. {title}"
    playlist: str = "{playlist}/{playlist_number:02d}. {artist} - {title}"


class DownloadConfig(BaseModel):
    quality: TrackArg = "high"
    path: Path = Path.home() / "Music" / "Tiddl"
    threads: int = 4
    singles_filter: SinglesFilter = "none"
    embed_lyrics: bool = False
    download_video: bool = False
    scan_path: Path | None = None


class AuthConfig(BaseModel):
    token: str = ""
    refresh_token: str = ""
    expires: int = 0
    user_id: str = ""
    country_code: str = ""


class CoverConfig(BaseModel):
    save: bool = False
    size: int = 1280
    filename: str = "cover.jpg"


class Config(BaseModel):
    template: TemplateConfig = TemplateConfig()
    download: DownloadConfig = DownloadConfig()
    cover: CoverConfig = CoverConfig()
    auth: AuthConfig = AuthConfig()
    omit_cache: bool = False

    def save(self):
        with open(CONFIG_PATH, "w") as f:
            f.write(self.model_dump_json(indent=CONFIG_INDENT))

    @classmethod
    def fromFile(cls):
        try:
            with CONFIG_PATH.open() as f:
                config = cls.model_validate_json(f.read())
        except FileNotFoundError:
            config = cls()

        config.save()
        return config
