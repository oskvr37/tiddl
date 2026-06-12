from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from tiddl.cli.commands.download import _apply_mtime


@pytest.fixture
def tmp_file(tmp_path: Path) -> Path:
    f = tmp_path / "track.flac"
    f.write_bytes(b"")
    return f


def test_update_mtime_calls_utime_with_none(tmp_file):
    with patch("tiddl.cli.commands.download.os.utime") as mock_utime:
        _apply_mtime(tmp_file, update_mtime=True, fav_mtime=False, fav_date_added=None)
    mock_utime.assert_called_once_with(tmp_file, None)


def test_fav_mtime_sets_timestamp(tmp_file):
    date_str = "2024-03-15T10:30:00"
    expected_ts = datetime.fromisoformat(date_str).timestamp()

    with patch("tiddl.cli.commands.download.os.utime") as mock_utime:
        _apply_mtime(tmp_file, update_mtime=False, fav_mtime=True, fav_date_added=date_str)
    mock_utime.assert_called_once_with(tmp_file, (expected_ts, expected_ts))


def test_update_mtime_wins_over_fav_mtime(tmp_file):
    """When update_mtime is set, fav_mtime is ignored and current time is used."""
    date_str = "2024-03-15T10:30:00"

    with patch("tiddl.cli.commands.download.os.utime") as mock_utime:
        _apply_mtime(tmp_file, update_mtime=True, fav_mtime=True, fav_date_added=date_str)
    mock_utime.assert_called_once_with(tmp_file, None)


def test_fav_mtime_without_date_does_nothing(tmp_file):
    with patch("tiddl.cli.commands.download.os.utime") as mock_utime:
        _apply_mtime(tmp_file, update_mtime=False, fav_mtime=True, fav_date_added=None)
    mock_utime.assert_not_called()


def test_both_disabled_does_nothing(tmp_file):
    with patch("tiddl.cli.commands.download.os.utime") as mock_utime:
        _apply_mtime(tmp_file, update_mtime=False, fav_mtime=False, fav_date_added="2024-03-15T10:30:00")
    mock_utime.assert_not_called()


def test_fav_mtime_sets_correct_timestamp_on_real_file(tmp_file):
    date_str = "2021-06-01T12:00:00+00:00"
    expected_ts = datetime.fromisoformat(date_str).timestamp()

    _apply_mtime(tmp_file, update_mtime=False, fav_mtime=True, fav_date_added=date_str)

    assert tmp_file.stat().st_mtime == pytest.approx(expected_ts, abs=1)
