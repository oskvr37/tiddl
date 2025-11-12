from logging import getLogger
from pathlib import Path
from pydantic import BaseModel, field_validator
from tomllib import loads as parse_toml
from typing import Literal

from tiddl.cli.const import APP_PATH

CONFIG_FILENAME = "config.toml"
DEFAULT_DOWNLOAD_PATH = Path.home() / "Music" / "tiddl"

TRACK_QUALITY_LITERAL = Literal["low", "normal", "high", "max"]
VIDEO_QUALITY_LITERAL = Literal["sd", "hd", "fhd"]
ARTIST_SINGLES_FILTER_LITERAL = Literal["none", "only", "include"]
VALID_M3U_RESOURCE_LITERAL = Literal["album", "playlist", "mix"]
VALID_RESOURCE_COVER_SAVE_LITERAL = Literal["track", "album", "playlist"]
VIDEOS_FILTER_LITERAL = Literal["none", "only", "allow"]

log = getLogger(__name__)


class Config(BaseModel):
    enable_cache: bool = True
    debug: bool = False

    class MetadataConfig(BaseModel):
        enable: bool = True
        lyrics: bool = False
        cover: bool = False

    metadata: MetadataConfig = MetadataConfig()

    class CoverConfig(BaseModel):
        save: bool = False
        size: int = 1280
        allowed: list[VALID_RESOURCE_COVER_SAVE_LITERAL] = []

        class CoverTemplatesConfig(BaseModel):
            track: str = ""
            album: str = ""
            playlist: str = ""

        templates: CoverTemplatesConfig = CoverTemplatesConfig()

    cover: CoverConfig = CoverConfig()

    class DownloadConfig(BaseModel):
        track_quality: TRACK_QUALITY_LITERAL = "high"
        video_quality: VIDEO_QUALITY_LITERAL = "fhd"
        skip_existing: bool = True
        threads_count: int = 4
        download_path: Path = DEFAULT_DOWNLOAD_PATH
        scan_path: Path = DEFAULT_DOWNLOAD_PATH
        singles_filter: ARTIST_SINGLES_FILTER_LITERAL = "none"
        videos_filter: VIDEOS_FILTER_LITERAL = "none"
        update_mtime: bool = False
        rewrite_metadata: bool = False

        def model_post_init(self, __context):
            # set scan path to download path when download path is non default
            if self.scan_path == DEFAULT_DOWNLOAD_PATH and self.download_path != DEFAULT_DOWNLOAD_PATH:
                self.scan_path = self.download_path

        @field_validator("download_path", "scan_path", mode="before")
        def str_to_path(cls, v):
            # convert to absolute, expand ~, normalize
            return Path(v).expanduser().resolve() if isinstance(v, str) else v

    download: DownloadConfig = DownloadConfig()

    class M3UConfig(BaseModel):
        # m3u playlists
        save: bool = False
        allowed: list[VALID_M3U_RESOURCE_LITERAL] = []

        class M3UTemplatesConfig(BaseModel):
            album: str = ""
            playlist: str = ""
            mix: str = ""

        templates: M3UTemplatesConfig = M3UTemplatesConfig()

    m3u: M3UConfig = M3UConfig()

    class TemplatesConfig(BaseModel):
        default: str = "{album.artist}/{album.title}/{item.title}"
        track: str = ""
        video: str = ""
        album: str = ""
        playlist: str = ""
        mix: str = ""

        def model_post_init(self, __context):
            assert self.default != "", "Default template cannot be empty."

            # override templates to default
            for field in ["track", "video", "album", "playlist", "mix"]:
                if getattr(self, field) == "":
                    setattr(self, field, self.default)

    templates: TemplatesConfig = TemplatesConfig()


def load_config_file(config_file: Path) -> Config:
    log.debug(f"loading '{config_file}'")

    if not config_file.exists():
        log.debug("config file not found, loading default config")
        return Config()

    toml_dict = parse_toml(config_file.read_text())
    config = Config.model_validate(toml_dict, strict=True)

    log.debug("loaded config from file")

    return config


CONFIG = load_config_file(APP_PATH / CONFIG_FILENAME)
log.debug(f"{CONFIG=}")
