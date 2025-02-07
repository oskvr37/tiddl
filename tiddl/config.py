from pydantic import BaseModel
from pathlib import Path

from tiddl.models.constants import TrackArg

HOME_PATH = Path.home()
CONFIG_PATH = HOME_PATH / "tiddl.json"
CONFIG_INDENT = 2


class TemplateConfig(BaseModel):
    track: str = "{artist} - {title}"
    album: str = "{album_artist}/{album}/{number:02d}. {title}"
    playlist: str = "{playlist}/{playlist_number:02d}. {artist} - {title}"


class DownloadConfig(BaseModel):
    quality: TrackArg = "high"
    path: Path = Path.home() / "Music" / "Tiddl"


class AuthConfig(BaseModel):
    token: str = ""
    refresh_token: str = ""
    expires: int = 0
    user_id: str = ""
    country_code: str = ""


class Config(BaseModel):
    template: TemplateConfig = TemplateConfig()
    download: DownloadConfig = DownloadConfig()
    auth: AuthConfig = AuthConfig()

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
