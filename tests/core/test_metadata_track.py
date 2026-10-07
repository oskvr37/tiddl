from pathlib import Path

from tiddl.core.api.models import Track
from tiddl.core.metadata import track as track_metadata


def test_add_track_metadata_keeps_primary_artist_first(monkeypatch):
    primary = Track.Artist(id=2, name="Zebra Artist", type="MAIN")
    guest = Track.Artist(id=1, name="Alpha Guest", type="FEATURED")
    collaborator = Track.Artist(id=3, name="Beta Collaborator", type="MAIN")
    track = Track.model_construct(
        title="Song",
        version=None,
        trackNumber=1,
        volumeNumber=1,
        copyright=None,
        artist=primary,
        artists=[guest, collaborator, primary],
        album=Track.Album(id=10, title="Album"),
        isrc="TEST123",
        bpm=None,
    )
    captured = []

    monkeypatch.setattr(
        track_metadata,
        "add_flac_metadata",
        lambda path, metadata: captured.append(metadata),
    )

    track_metadata.add_track_metadata(Path("song.flac"), track)

    assert captured[0].artists == [
        "Zebra Artist",
        "Alpha Guest",
        "Beta Collaborator",
    ]


def test_add_track_metadata_preserves_artist_order_without_primary(monkeypatch):
    first = Track.Artist(id=1, name="Zebra Artist", type="MAIN")
    second = Track.Artist(id=2, name="Alpha Artist", type="MAIN")
    track = Track.model_construct(
        title="Song",
        version=None,
        trackNumber=1,
        volumeNumber=1,
        copyright=None,
        artist=None,
        artists=[first, second],
        album=Track.Album(id=10, title="Album"),
        isrc="TEST123",
        bpm=None,
    )
    captured = []

    monkeypatch.setattr(
        track_metadata,
        "add_flac_metadata",
        lambda path, metadata: captured.append(metadata),
    )

    track_metadata.add_track_metadata(Path("song.flac"), track)

    assert captured[0].artists == ["Zebra Artist", "Alpha Artist"]
