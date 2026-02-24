import pytest
from pydantic import ValidationError

from tiddl.core.api.models.resources import Video


# Minimal valid payload shared across tests
BASE_VIDEO = {
    "id": 123,
    "title": "Test Video",
    "volumeNumber": 1,
    "trackNumber": 1,
    "duration": 180,
    "quality": "MP4_1080P",
    "streamReady": True,
    "adSupportedStreamReady": False,
    "djReady": False,
    "stemReady": False,
    "allowStreaming": True,
    "explicit": False,
    "popularity": 50,
    "type": "Music Video",
    "adsPrePaywallOnly": False,
    "artists": [],
}


def test_video_null_image_id():
    """imageId=null should be accepted (Tidal returns this for some videos)."""
    video = Video.model_validate({**BASE_VIDEO, "imageId": None})
    assert video.imageId is None


def test_video_missing_image_id():
    """imageId absent entirely should default to None."""
    video = Video.model_validate(BASE_VIDEO)
    assert video.imageId is None


def test_video_valid_image_id():
    """A normal imageId string should still be accepted."""
    video = Video.model_validate({**BASE_VIDEO, "imageId": "abc123"})
    assert video.imageId == "abc123"


def test_video_album_missing_required_fields():
    """album object present but missing id/title/cover should be accepted."""
    payload = {
        **BASE_VIDEO,
        "album": {"vibrantColor": None},
    }
    video = Video.model_validate(payload)
    assert video.album is not None
    assert video.album.id is None
    assert video.album.title is None
    assert video.album.cover is None


def test_video_album_none():
    """album=null should still be accepted (existing behaviour)."""
    video = Video.model_validate({**BASE_VIDEO, "album": None})
    assert video.album is None


def test_video_album_fully_populated():
    """A fully populated album object should still parse correctly."""
    payload = {
        **BASE_VIDEO,
        "album": {
            "id": 42,
            "title": "Greatest Hits",
            "cover": "cover-uuid",
        },
    }
    video = Video.model_validate(payload)
    assert video.album is not None
    assert video.album.id == 42
    assert video.album.title == "Greatest Hits"
    assert video.album.cover == "cover-uuid"


def test_video_still_requires_core_fields():
    """Removing a genuinely required field (title) should still raise."""
    payload = {k: v for k, v in BASE_VIDEO.items() if k != "title"}
    with pytest.raises(ValidationError):
        Video.model_validate(payload)
