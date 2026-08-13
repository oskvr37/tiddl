import asyncio
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from tiddl.cli.commands.download.downloader import Downloader
from tiddl.core.api.models import Track


@pytest.mark.parametrize(
    ("atmos_filter", "audio_modes", "tags", "expected_profile"),
    [
        ("none", ["DOLBY_ATMOS"], ["HIRES_LOSSLESS"], "hires"),
        ("only", ["STEREO"], ["LOSSLESS"], "atmos"),
        ("allow", ["STEREO"], ["DOLBY_ATMOS"], "atmos"),
        ("allow", ["STEREO"], ["HIRES_LOSSLESS"], "hires"),
    ],
)
def test_get_track_api_selects_capability_profile(
    mocker: MockerFixture,
    tmp_path,
    atmos_filter,
    audio_modes,
    tags,
    expected_profile,
):
    catalog_api = mocker.Mock()
    playback_api = mocker.Mock()
    get_playback_api = mocker.Mock(return_value=playback_api)
    downloader = Downloader(
        tidal_api=catalog_api,
        threads_count=1,
        rich_output=mocker.Mock(),
        track_quality="max",
        video_quality="fhd",
        videos_filter="allow",
        skip_existing=True,
        download_path=tmp_path,
        scan_path=tmp_path,
        dolby_atmos_filter=atmos_filter,
        get_playback_api=get_playback_api,
    )
    track = mocker.Mock(
        audioModes=audio_modes,
        mediaMetadata=mocker.Mock(tags=tags),
    )

    assert downloader.get_track_api(track) is playback_api
    get_playback_api.assert_called_once_with(expected_profile)


def test_get_track_api_preserves_legacy_api(mocker: MockerFixture, tmp_path):
    catalog_api = mocker.Mock()
    downloader = Downloader(
        tidal_api=catalog_api,
        threads_count=1,
        rich_output=mocker.Mock(),
        track_quality="max",
        video_quality="fhd",
        videos_filter="allow",
        skip_existing=True,
        download_path=tmp_path,
        scan_path=tmp_path,
    )

    assert downloader.get_track_api(mocker.Mock()) is catalog_api


def test_atmos_download_checks_m4a_instead_of_existing_max_flac(
    mocker: MockerFixture,
    tmp_path,
):
    get_playback_api = mocker.Mock()
    downloader = Downloader(
        tidal_api=mocker.Mock(),
        threads_count=1,
        rich_output=mocker.Mock(),
        track_quality="max",
        video_quality="fhd",
        videos_filter="allow",
        skip_existing=True,
        download_path=tmp_path,
        scan_path=tmp_path,
        dolby_atmos_filter="only",
        get_playback_api=get_playback_api,
    )
    track = mocker.Mock(spec=Track)
    track.allowStreaming = True
    track.title = "Track"
    track.id = 1
    track.audioQuality = "HI_RES_LOSSLESS"
    track.audioModes = ["DOLBY_ATMOS"]
    track.mediaMetadata = mocker.Mock(tags=["HIRES_LOSSLESS", "DOLBY_ATMOS"])
    track.album = mocker.Mock(vibrantColor=None)
    file_path = Path("track")
    (tmp_path / file_path.with_suffix(".flac")).touch()
    atmos_path = tmp_path / file_path.with_suffix(".m4a")
    atmos_path.touch()

    item_path, was_downloaded = asyncio.run(downloader.download(track, file_path))

    assert item_path == atmos_path
    assert not was_downloaded
    get_playback_api.assert_not_called()
