from dataclasses import dataclass
from datetime import datetime

from tiddl.core.api.models import Track, Video, Album, Playlist
from tiddl.core.utils.sanitize import sanitize_string


@dataclass(slots=True)
class AlbumTemplate:
    id: int
    title: str
    artist: str
    artists: str
    date: datetime


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
            # FIX audio quality should be returned from `get_existing_track_filename`.
            # `item.audioQuality` tells highest quality of track - not quality we downloaded
            quality = item.audioQuality or ""
        else:  # Video
            version = ""
            copyright_ = ""
            bpm = 0
            isrc = ""
            quality = item.quality or ""

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
        )
        | extra
        | custom_fields
    )

    path: str = "/".join(
        [sanitize_string(segment.format(**data)) for segment in template.split("/")]
    )

    if with_asterisk_ext:
        path += ".*"

    return path
