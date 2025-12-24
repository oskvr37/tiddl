import re
from dataclasses import dataclass
from datetime import datetime

from tiddl.core.api.models import Track, Video, Album, Playlist
from tiddl.core.utils.sanitize import sanitize_string


def _clean_segment(text: str) -> str:
    """
    Clean a single path segment using sanitize_string plus extra rules
    to keep it safe for Windows / NAS filesystems.

    - Uses sanitize_string for base cleanup.
    - Collapses multiple dots ("..", "...") into a single dot.
    - Removes trailing dots and spaces (Windows forbids them).
    - Collapses multiple spaces into one.
    - Ensures the segment is never empty (uses "_" as fallback).
    """

    text = sanitize_string(text)
    text = re.sub(r"\.{2,}", ".", text)
    text = text.rstrip(" .")
    text = re.sub(r"\s{2,}", " ", text)
    text = text.strip()

    return text or "_"


class Explicit:
    def __init__(self, value: bool | None):
        self.value = value

    def __format__(self, format_spec: str):
        if self.value is None:
            return ""

        features = format_spec.split("; ")

        def get_base():
            for feature in features:
                match feature:
                    case "long":
                        return "explicit" if self.value else ""
                    case "full":
                        return "explicit" if self.value else "clean"

            return "E" if self.value else ""

        base = get_base()

        for feature in features:
            match feature:
                case "upper":
                    return base.upper()

        return base


class UserFormat:
    def __init__(self, value: bool) -> None:
        self.value = value

    def __format__(self, format_spec: str) -> str:
        return format_spec if self.value is True else ""


@dataclass(slots=True)
class AlbumTemplate:
    id: int
    title: str
    artist: str
    artists: str
    date: datetime
    explicit: Explicit
    master: UserFormat
    release: str


@dataclass(slots=True)
class ItemTemplate:
    id: int
    title: str
    title_version: str
    number: int
    volume: int
    version: str
    copyright: str
    bpm: int
    isrc: str
    quality: str
    artist: str
    artists: str
    features: str
    artists_with_features: str
    explicit: Explicit
    dolby: UserFormat


@dataclass(slots=True)
class PlaylistTemplate:
    uuid: str
    title: str
    index: int
    created: datetime
    updated: datetime


def generate_template_data(
    item: Track | Video | None = None,
    album: Album | None = None,
    playlist: Playlist | None = None,
    playlist_index: int = 0,
    quality: str = "",
) -> dict[str, ItemTemplate | AlbumTemplate | PlaylistTemplate | None]:
    """Normalize Tidal API Track/Video + Album data into safe templates."""

    item_template = None
    if item:
        main_artists = sorted(
            [a.name for a in (item.artists or []) if a.type == "MAIN"]
        )
        featured_artists = sorted(
            [a.name for a in (item.artists or []) if a.type == "FEATURED"]
        )

        if isinstance(item, Track):
            version = item.version or ""
            copyright_ = item.copyright or ""
            bpm = item.bpm or 0
            isrc = item.isrc or ""
            dolby = UserFormat("DOLBY_ATMOS" in item.mediaMetadata.tags)
        else:  # Video
            version = ""
            copyright_ = ""
            bpm = 0
            isrc = ""
            dolby = UserFormat(False)

        item_template = ItemTemplate(
            id=item.id,
            title=item.title,
            title_version=f"{item.title} ({version})" if version else item.title,
            number=item.trackNumber,
            volume=item.volumeNumber,
            version=version,
            copyright=copyright_,
            bpm=bpm,
            isrc=isrc,
            quality=quality,
            artist=item.artist.name if item.artist else "",
            artists=", ".join(main_artists),
            features=", ".join(featured_artists),
            artists_with_features=", ".join(main_artists + featured_artists),
            explicit=Explicit(getattr(item, "explicit", None)),
            dolby=dolby,
        )

    album_template = None
    if album:
        album_template = AlbumTemplate(
            id=album.id,
            title=album.title,
            artist=album.artist.name if album.artist else "",
            artists=", ".join(
                a.name for a in (album.artists or []) if a.type == "MAIN"
            ),
            date=album.releaseDate,
            explicit=Explicit(getattr(album, "explicit", None)),
            master=UserFormat(
                "HIRES_LOSSLESS" in album.mediaMetadata.tags and quality == "MAX"
            ),
            release=album.type,
        )

    playlist_template = None
    if playlist:
        playlist_template = PlaylistTemplate(
            uuid=playlist.uuid,
            title=playlist.title,
            index=playlist_index,
            created=datetime.fromisoformat(playlist.created),
            updated=datetime.fromisoformat(playlist.lastUpdated),
        )

    templates: dict[str, ItemTemplate | AlbumTemplate | PlaylistTemplate | None] = {
        "item": item_template,
        "album": album_template,
        "playlist": playlist_template,
    }

    return templates


def format_template(
    template: str,
    item: Track | Video | None = None,
    album: Album | None = None,
    playlist: Playlist | None = None,
    playlist_index: int = 0,
    quality: str = "",
    with_asterisk_ext: bool = True,
    **extra,
) -> str:
    """
    Raises `AttributeError` on invalid template.
    """

    custom_fields = {"now": datetime.now()}

    data = (
        generate_template_data(
            item=item,
            album=album,
            playlist=playlist,
            playlist_index=playlist_index,
            quality=quality,
        )
        | extra
        | custom_fields
    )

    segments: list[str] = []

    for raw_segment in template.split("/"):
        formatted = raw_segment.format(**data)
        cleaned = _clean_segment(formatted)
        segments.append(cleaned)

    path = "/".join(segments)

    if with_asterisk_ext:
        path += ".*"

    return path
