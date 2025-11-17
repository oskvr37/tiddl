from dataclasses import dataclass
from datetime import datetime

from tiddl.core.api.models import Track, Video, Album, Playlist
from tiddl.core.utils.sanitize import sanitize_string


class Explicit:
    def __init__(self, value: bool | None):
        self.value = value

    def __format__(self, format_spec: str):
        if self.value is None:
            return ""

        features = format_spec.split(",")

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
            master=UserFormat("HIRES_LOSSLESS" in album.mediaMetadata.tags),
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
    with_asterisk_ext=True,
    **extra,
) -> str:
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

    path: str = "/".join(
        [
            sanitize_string(segment.format(**data)).strip()
            for segment in template.split("/")
        ]
    )

    if with_asterisk_ext:
        path += ".*"

    return path
