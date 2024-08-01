from typing import TypedDict, Literal, List, get_args

from .types.track import Track

RESOURCE = Literal["track", "album", "artist", "playlist"]
RESOURCE_LIST: List[RESOURCE] = list(get_args(RESOURCE))


def parseURL(url: str) -> tuple[RESOURCE, str]:
    # remove trailing slash
    url = url.rstrip("/")
    # remove params
    url = url.split("?")[0]

    fragments = url.split("/")

    if len(fragments) < 2:
        raise ValueError(f"Invalid input: {url}")

    parsed_type, parsed_id = fragments[-2], fragments[-1]

    if parsed_type not in RESOURCE_LIST:
        raise ValueError(f"Invalid resource type: {parsed_type} ({url})")

    return parsed_type, parsed_id


class FormattedTrack(TypedDict):
    id: int
    title: str
    number: int
    artist: str
    album: str
    artists: str


def _formatTrackDict(track: Track) -> FormattedTrack:
    artists = [artist["name"] for artist in track["artists"]]
    formatted_track: FormattedTrack = {
        "album": track["album"]["title"],
        "artist": track["artist"]["name"],
        "artists": ", ".join(artists),
        "id": track["id"],
        "title": track["title"],
        "number": track["trackNumber"],
    }
    return formatted_track


def formatFilename(template: str, track: Track) -> str:
    formatted_track = _formatTrackDict(track)
    try:
        return template.format(**formatted_track)
    except KeyError as e:
        missing_key = e.args[0]
        raise ValueError(f"Missing key in track dictionary: {missing_key}")
