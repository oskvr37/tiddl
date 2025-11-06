from logging import getLogger
from pathlib import Path
from tiddl.core.api.models import TrackQuality

log = getLogger(__name__)


def get_existing_track_filename(
    track_quality: TrackQuality, download_quality: TrackQuality, file_name: Path
) -> Path:
    """
    Predict track extension.
    """

    FLAC_QUALITIES: list[TrackQuality] = ["LOSSLESS", "HI_RES_LOSSLESS"]

    if download_quality in FLAC_QUALITIES and track_quality in FLAC_QUALITIES:
        extension = ".flac"
    else:
        extension = ".m4a"

    full_file_name = file_name.with_suffix(extension)

    log.debug(f"{track_quality=}, {download_quality=}, {file_name=}, {full_file_name=}")

    return full_file_name
