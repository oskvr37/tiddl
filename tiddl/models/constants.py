from typing import Literal

TrackQuality = Literal["LOW", "HIGH", "LOSSLESS", "HI_RES_LOSSLESS"]
TrackArg = Literal["low", "normal", "high", "master"]

ARG_TO_QUALITY: dict[TrackArg, TrackQuality] = {
    "low": "LOW",
    "normal": "HIGH",
    "high": "LOSSLESS",
    "master": "HI_RES_LOSSLESS",
}

QUALITY_TO_ARG = {v: k for k, v in ARG_TO_QUALITY.items()}
