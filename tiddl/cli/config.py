import os
from logging import getLogger
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from tomllib import loads as parse_toml

from tiddl.cli.const import APP_PATH
from tiddl.core.utils.const import TRACK_QUALITY_LITERAL, VIDEO_QUALITY_LITERAL

CONFIG_FILENAME = "config.toml"
DEFAULT_DOWNLOAD_PATH = Path.home() / "Music" / "tiddl"

ARTIST_SINGLES_FILTER_LITERAL = Literal["none", "only", "include"]
VALID_M3U_RESOURCE_LITERAL = Literal["album", "playlist", "mix"]
VALID_RESOURCE_COVER_SAVE_LITERAL = Literal["track", "album", "playlist"]
VIDEOS_FILTER_LITERAL = Literal["none", "only", "allow"]

log = getLogger(__name__)

# --- Nested Models ---

class MetadataConfig(BaseModel):
    enable: bool = True
    lyrics: bool = False
    cover: bool = False
    album_review: bool = False

class CoverTemplatesConfig(BaseModel):
    track: str = ""
    album: str = ""
    playlist: str = ""

class CoverConfig(BaseModel):
    save: bool = False
    size: int = 1280
    allowed: list[VALID_RESOURCE_COVER_SAVE_LITERAL] = []
    templates: CoverTemplatesConfig = CoverTemplatesConfig()

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
        if self.scan_path == DEFAULT_DOWNLOAD_PATH and self.download_path != DEFAULT_DOWNLOAD_PATH:
            self.scan_path = self.download_path

    @field_validator("download_path", "scan_path", mode="before")
    @classmethod
    def str_to_path(cls, v):
        return Path(v).expanduser().resolve() if isinstance(v, (str, Path)) else v

class M3UTemplatesConfig(BaseModel):
    album: str = ""
    playlist: str = ""
    mix: str = ""

class M3UConfig(BaseModel):
    save: bool = False
    allowed: list[VALID_M3U_RESOURCE_LITERAL] = []
    templates: M3UTemplatesConfig = M3UTemplatesConfig()

class TemplatesConfig(BaseModel):
    default: str = "{album.artist}/{album.title}/{item.title}"
    track: str = ""
    video: str = ""
    album: str = ""
    playlist: str = ""
    mix: str = ""

    def model_post_init(self, __context):
        assert self.default != "", "Default template cannot be empty."
        for field in ["track", "video", "album", "playlist", "mix"]:
            if getattr(self, field) == "":
                setattr(self, field, self.default)

# --- Main Settings Container ---

class Config(BaseSettings):
    # Pydantic Settings magic:
    # 1. Environment variables (prefixed with TIDDL_) take priority
    # 2. Then the TOML file
    # 3. Then defaults
    model_config = SettingsConfigDict(
        env_prefix="TIDDL_", 
        env_nested_delimiter="__",
        extra="ignore"
    )

    enable_cache: bool = True
    debug: bool = False
    metadata: MetadataConfig = MetadataConfig()
    cover: CoverConfig = CoverConfig()
    download: DownloadConfig = DownloadConfig()
    m3u: M3UConfig = M3UConfig()
    templates: TemplatesConfig = TemplatesConfig()

def load_config(config_path: Path) -> Config:
    """
    Loads config with the following priority:
    1. Environment Variables (TIDDL_*)
    2. config.toml file
    3. Default values
    """
    toml_data = {}
    if config_path.exists():
        log.debug(f"Loading config file: {config_path}")
        try:
            toml_data = parse_toml(config_path.read_text())
        except Exception as e:
            log.warning(f"Failed to parse {config_path}: {e}")
    else:
        log.debug("Config file not found, relying on Env/Defaults")

    # BaseSettings handles the merging of toml_data and Env Vars automatically
    return Config(**toml_data)

# Initialization
CONFIG = load_config(APP_PATH / CONFIG_FILENAME)
log.debug(f"Config initialized: {CONFIG.model_dump()}")
