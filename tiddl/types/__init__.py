from typing import TypedDict, Literal

from .api import *
from .playlist import *
from .track import *

TrackArg = Literal["low", "normal", "high", "master"]


class QualityDetails(TypedDict):
    name: str
    details: str
    arg: TrackArg


TRACK_QUALITY: dict[TrackQuality, QualityDetails] = {
    "LOW": {"name": "Low", "details": "96 kbps", "arg": "low"},
    "HIGH": {"name": "Low", "details": "320 kbps", "arg": "normal"},
    "LOSSLESS": {"name": "High", "details": "16-bit, 44.1 kHz", "arg": "high"},
    "HI_RES_LOSSLESS": {
        "name": "Max",
        "details": "Up to 24-bit, 192 kHz",
        "arg": "master",
    },
}
