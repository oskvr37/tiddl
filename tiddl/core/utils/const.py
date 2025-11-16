from typing import Literal

from tiddl.core.api.models import TrackQuality, VideoQuality


TRACK_QUALITY_LITERAL = Literal["low", "normal", "high", "max"]
VIDEO_QUALITY_LITERAL = Literal["sd", "hd", "fhd"]

track_qualities: dict[TRACK_QUALITY_LITERAL, TrackQuality] = {
    "low": "LOW",
    "normal": "HIGH",
    "high": "LOSSLESS",
    "max": "HI_RES_LOSSLESS",
}

video_qualities: dict[VIDEO_QUALITY_LITERAL, VideoQuality] = {
    "sd": "LOW",
    "hd": "MEDIUM",
    "fhd": "HIGH",
}
