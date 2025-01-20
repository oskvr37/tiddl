import re
from urllib.parse import urlparse
from typing import Literal, get_args

from tiddl.models import Track, QUALITY_TO_ARG

ResourceTypeLiteral = Literal["track", "album", "playlist", "artist"]


class TidalResource:
    """
    A parser for Tidal resource URLs or strings.

    Extracts the resource type (e.g., "track", "album") and resource ID
    from a given input string. The input string can either be a full URL or a
    shorthand string in the format "resource_type/resource_id" (e.g., "track/12345678").
    """

    resource: str
    resource_type: ResourceTypeLiteral
    resource_id: str
    url: str

    def __init__(self, resource: str) -> None:
        self.resource = resource

        path = urlparse(self.resource).path
        resource_type, resource_id = path.split("/")[-2:]

        if resource_type not in get_args(ResourceTypeLiteral):
            raise ValueError(f"Invalid resource type: {resource_type}")

        self.resource_type = resource_type  # type: ignore

        if not resource_id.isdigit() and self.resource_type != "playlist":
            raise ValueError(f"Invalid resource id: {resource_id}")

        self.resource_id = resource_id

        self.url = f"https://listen.tidal.com/{self.resource_type}/{self.resource_id}"

    def __str__(self) -> str:
        return f"{self.resource_type}/{self.resource_id}"


def sanitizeString(string: str) -> str:
    pattern = r'[\\/:"*?<>|]+'
    return re.sub(pattern, "", string)


def formatTrack(template: str, track: Track, date_format="%x") -> str:
    disallowed_chars = r'[\\:"*?<>|]+'
    invalid_chars = re.findall(disallowed_chars, template)

    if invalid_chars:
        raise ValueError(
            f"Template '{template}' contains disallowed characters: {' '.join(sorted(set(invalid_chars)))}"
        )

    artist = track.artist.name if track.artist else ""
    features = [
        track_artist.name
        for track_artist in track.artists
        if track_artist.name != artist
    ]

    track_dict: dict[str, str] = {
        "id": str(track.id),
        "title": track.title,
        "version": track.version or "",
        "artist": artist,
        "artists": ", ".join(features + [artist]),
        "features": ", ".join(features),
        "album": track.album.title,
        "number": str(track.trackNumber),
        "disc": str(track.volumeNumber),
        "date": (
            track.streamStartDate.strftime(date_format).replace("/", "-")
            if track.streamStartDate
            else ""
        ),
        "year": track.streamStartDate.strftime("%Y") if track.streamStartDate else "",
        "playlist_number": str(track.playlistNumber or ""),
        "bpm": str(track.bpm or ""),
        "quality": QUALITY_TO_ARG[track.audioQuality],
    }

    for key, value in track_dict.items():
        track_dict[key] = sanitizeString(value)

    return template.format(**track_dict)
