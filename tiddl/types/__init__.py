from typing import TypedDict, Literal

from .api import *
from .track import *
from .auth import *


TrackArg = Literal["low", "normal", "high", "master"]


class QualityDetails(TypedDict):
    name: str
    details: str
    quality: TrackQuality


TRACK_QUALITY: dict[TrackArg, QualityDetails] = {
    "low": {"name": "Low", "details": "96 kbps", "quality": "LOW"},
    "normal": {"name": "Low", "details": "320 kbps", "quality": "HIGH"},
    "high": {"name": "High", "details": "16-bit, 44.1 kHz", "quality": "LOSSLESS"},
    "master": {
        "name": "Max",
        "details": "Up to 24-bit, 192 kHz",
        "quality": "HI_RES_LOSSLESS",
    },
}
