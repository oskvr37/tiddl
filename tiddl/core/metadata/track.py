from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

from mutagen.flac import FLAC as MutagenFLAC, Picture
from mutagen.easymp4 import EasyMP4 as MutagenEasyMP4
from mutagen.mp4 import MP4 as MutagenMP4, MP4Cover

from tiddl.core.api.models import AlbumItemsCredits, Track


@dataclass(slots=True)
class Metadata:
    title: str
    track_number: str
    disc_number: str
    copyright: str | None
    album_artist: str
    artists: str
    album_title: str
    date: str
    isrc: str
    bpm: str | None = None
    lyrics: str | None = None
    credits: list[AlbumItemsCredits.ItemWithCredits.CreditsEntry] = field(
        default_factory=list
    )
    cover_data: bytes | None = None
    comment: str = ""


def add_flac_metadata(track_path: Path, metadata: Metadata) -> None:
    mutagen = MutagenFLAC(track_path)

    if metadata.cover_data:
        picture = Picture()
        picture.data = metadata.cover_data
        picture.mime = "image/jpeg"
        picture.type = 3  # front cover
        mutagen.add_picture(picture)

    if metadata.date:
        date = datetime.fromisoformat(metadata.date)
    else:
        date = None

    mutagen.update(
        {
            "TITLE": metadata.title,
            "TRACKNUMBER": metadata.track_number,
            "DISCNUMBER": metadata.disc_number,
            "ALBUM": metadata.album_title,
            "ALBUMARTIST": metadata.album_artist,
            "ARTIST": metadata.artists,
            "DATE": str(date) if date else "",
            "YEAR": (str(date.year) if date else ""),
            "COPYRIGHT": metadata.copyright or "",
            "ISRC": metadata.isrc,
            "COMMENT": metadata.comment,
        }
    )

    if metadata.bpm:
        mutagen["BPM"] = metadata.bpm
    if metadata.lyrics:
        mutagen["LYRICS"] = metadata.lyrics

    for entry in metadata.credits:
        mutagen[entry.type.upper()] = [c.name for c in entry.contributors]

    mutagen.save()


def add_m4a_metadata(track_path: Path, metadata: Metadata) -> None:
    mutagen = MutagenMP4(track_path)

    if metadata.cover_data:
        mutagen["covr"] = [
            MP4Cover(metadata.cover_data, imageformat=MP4Cover.FORMAT_JPEG)
        ]

    if metadata.lyrics:
        mutagen["\xa9lyr"] = [metadata.lyrics]

    mutagen.save()

    mutagen = MutagenEasyMP4(track_path)

    mutagen.update(
        {
            "title": metadata.title,
            "tracknumber": metadata.track_number,
            "discnumber": metadata.disc_number,
            "album": metadata.album_title,
            "albumartist": metadata.album_artist,
            "artist": metadata.artists,
            "date": metadata.date,
            "copyright": metadata.copyright or "",
            "comment": metadata.comment,
        }
    )

    if metadata.bpm:
        mutagen["bpm"] = metadata.bpm

    mutagen.save()


def sort_credits_contributors(
    entries: list[AlbumItemsCredits.ItemWithCredits.CreditsEntry],
):
    """
    Sorts the contributors within each CreditsEntry alphabetically by surname.

    It assumes the surname is the last word in the contributor's name.
    """

    def get_surname(name: str) -> str:
        parts = name.split()
        return parts[-1] if parts else ""

    for entry in entries:
        entry.contributors.sort(
            key=lambda contributor: get_surname(contributor.name).lower()
        )


def add_track_metadata(
    path: Path,
    track: Track,
    date: str = "",
    album_artist: str = "",
    lyrics: str = "",
    cover_data: bytes | None = None,
    credits_contributors: (
        list[AlbumItemsCredits.ItemWithCredits.CreditsEntry] | None
    ) = None,
    comment: str = "",
) -> None:
    """Add FLAC or M4A metadata based on file extension."""

    if credits_contributors is None:
        credits_contributors = []

    sort_credits_contributors(credits_contributors)

    metadata = Metadata(
        title=f"{track.title} ({track.version})" if track.version else track.title,
        track_number=str(track.trackNumber),
        disc_number=str(track.volumeNumber),
        copyright=track.copyright,
        album_artist=album_artist,
        artists="; ".join(sorted(a.name.strip() for a in track.artists)),
        album_title=track.album.title,
        date=date,
        isrc=track.isrc,
        bpm=str(track.bpm or ""),
        lyrics=lyrics or None,
        cover_data=cover_data,
        credits=credits_contributors,
        comment=comment,
    )

    ext = path.suffix.lower()

    if ext == ".flac":
        add_flac_metadata(path, metadata)
    elif ext == ".m4a":
        add_m4a_metadata(path, metadata)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
