import asyncio
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from tiddl.cli.commands.download.downloader import Downloader
from tiddl.core.api import TidalAPI
from tiddl.core.api.models import Track


class StopAfterStreamRequest(Exception):
    pass


@pytest.fixture
def track(mocker: MockerFixture):
    track = mocker.Mock(spec=Track)
    track.id = 1
    track.title = "Track"
    track.allowStreaming = True
    track.audioQuality = "LOSSLESS"
    track.album = mocker.Mock(vibrantColor=None)
    return track


def make_downloader(mocker: MockerFixture, tmp_path: Path, dolby_atmos_filter):
    api = mocker.Mock(spec=TidalAPI)
    # stop right after the stream request, the test only checks how it was made
    api.get_track_stream.side_effect = StopAfterStreamRequest
    downloader = Downloader(
        tidal_api=api,
        threads_count=1,
        rich_output=mocker.Mock(),
        track_quality="high",
        video_quality="fhd",
        videos_filter="none",
        skip_existing=True,
        download_path=tmp_path,
        scan_path=tmp_path,
        dolby_atmos_filter=dolby_atmos_filter,
    )
    return downloader, api


@pytest.mark.parametrize(
    "dolby_atmos_filter, immersive_audio",
    [("none", False), ("allow", None), ("only", None)],
)
def test_track_stream_requests_audio_mode_from_filter(
    mocker: MockerFixture,
    tmp_path: Path,
    track,
    dolby_atmos_filter,
    immersive_audio,
):
    downloader, api = make_downloader(mocker, tmp_path, dolby_atmos_filter)

    with pytest.raises(StopAfterStreamRequest):
        asyncio.run(downloader.download(track, Path("track")))

    api.get_track_stream.assert_called_once_with(
        track_id=1, quality="LOSSLESS", immersive_audio=immersive_audio
    )
