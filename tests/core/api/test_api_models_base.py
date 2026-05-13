import pytest
from pydantic import ValidationError

from tiddl.core.api.models.base import FavoriteAlbumsItems, FavoriteTracksItems, FavoriteVideosItems


BASE_TRACK = {
    "id": 1,
    "title": "Test Track",
    "duration": 180,
    "replayGain": 0.0,
    "peak": 1.0,
    "allowStreaming": True,
    "streamReady": True,
    "adSupportedStreamReady": False,
    "djReady": False,
    "stemReady": False,
    "premiumStreamingOnly": False,
    "trackNumber": 1,
    "volumeNumber": 1,
    "popularity": 50,
    "url": "https://tidal.com/track/1",
    "isrc": "USAAA0000001",
    "editable": False,
    "explicit": False,
    "audioQuality": "HIGH",
    "audioModes": ["STEREO"],
    "mediaMetadata": {"tags": []},
    "artists": [],
    "album": {"id": 1, "title": "Test Album"},
}

BASE_VIDEO = {
    "id": 2,
    "title": "Test Video",
    "volumeNumber": 1,
    "trackNumber": 1,
    "duration": 240,
    "quality": "MP4_1080P",
    "streamReady": True,
    "adSupportedStreamReady": False,
    "djReady": False,
    "stemReady": False,
    "allowStreaming": True,
    "explicit": False,
    "popularity": 30,
    "type": "Music Video",
    "adsPrePaywallOnly": False,
    "artists": [],
}

FAVORITE_TRACKS_PAYLOAD = {
    "limit": 20,
    "offset": 0,
    "totalNumberOfItems": 1,
    "items": [
        {"item": BASE_TRACK, "type": "track", "created": "2024-03-15T10:30:00"},
    ],
}

FAVORITE_VIDEOS_PAYLOAD = {
    "limit": 20,
    "offset": 0,
    "totalNumberOfItems": 1,
    "items": [
        {"item": BASE_VIDEO, "type": "video", "created": "2024-06-01T08:00:00"},
    ],
}


def test_favorite_tracks_items_parses():
    result = FavoriteTracksItems.model_validate(FAVORITE_TRACKS_PAYLOAD)
    assert result.totalNumberOfItems == 1
    assert len(result.items) == 1
    assert result.items[0].item.title == "Test Track"
    assert result.items[0].created == "2024-03-15T10:30:00"


def test_favorite_videos_items_parses():
    result = FavoriteVideosItems.model_validate(FAVORITE_VIDEOS_PAYLOAD)
    assert result.totalNumberOfItems == 1
    assert len(result.items) == 1
    assert result.items[0].item.title == "Test Video"
    assert result.items[0].created == "2024-06-01T08:00:00"


def test_favorite_tracks_missing_created_raises():
    payload = {
        **FAVORITE_TRACKS_PAYLOAD,
        "items": [{"item": BASE_TRACK, "type": "track"}],
    }
    with pytest.raises(ValidationError):
        FavoriteTracksItems.model_validate(payload)


def test_favorite_tracks_pagination_fields():
    payload = {**FAVORITE_TRACKS_PAYLOAD, "limit": 5, "offset": 10, "totalNumberOfItems": 50}
    result = FavoriteTracksItems.model_validate(payload)
    assert result.limit == 5
    assert result.offset == 10
    assert result.totalNumberOfItems == 50


BASE_ALBUM = {
    "id": 10,
    "title": "Test Album",
    "duration": 3600,
    "streamReady": True,
    "adSupportedStreamReady": False,
    "djReady": False,
    "stemReady": False,
    "allowStreaming": True,
    "premiumStreamingOnly": False,
    "numberOfTracks": 10,
    "numberOfVideos": 0,
    "numberOfVolumes": 1,
    "type": "ALBUM",
    "url": "https://tidal.com/album/10",
    "explicit": False,
    "popularity": 80,
    "audioQuality": "LOSSLESS",
    "audioModes": ["STEREO"],
    "mediaMetadata": {"tags": ["LOSSLESS"]},
    "artists": [],
}

FAVORITE_ALBUMS_PAYLOAD = {
    "limit": 20,
    "offset": 0,
    "totalNumberOfItems": 1,
    "items": [
        {"item": BASE_ALBUM, "type": "album", "created": "2023-11-20T15:45:00"},
    ],
}


def test_favorite_albums_items_parses():
    result = FavoriteAlbumsItems.model_validate(FAVORITE_ALBUMS_PAYLOAD)
    assert result.totalNumberOfItems == 1
    assert result.items[0].item.title == "Test Album"
    assert result.items[0].created == "2023-11-20T15:45:00"


def test_favorite_albums_missing_created_raises():
    payload = {
        **FAVORITE_ALBUMS_PAYLOAD,
        "items": [{"item": BASE_ALBUM, "type": "album"}],
    }
    with pytest.raises(ValidationError):
        FavoriteAlbumsItems.model_validate(payload)
