import pytest

from pathlib import Path
from requests import exceptions as requests_exceptions

from tiddl.cli.commands.download.report import (
    EXIT_PARTIAL,
    DownloadReport,
    count_kinds,
    is_transient_error,
    keep_existing_m3u,
)
from tiddl.core.api import ApiError, RateLimitError


def test_exit_partial_is_not_success():
    assert EXIT_PARTIAL != 0


@pytest.mark.parametrize(
    "error",
    [
        RateLimitError(),
        ApiError(status=429, subStatus="0", userMessage="rate limited"),
        ApiError(status=503, subStatus="0", userMessage="unavailable"),
        requests_exceptions.ConnectionError("connection reset"),
        requests_exceptions.Timeout("timed out"),
        TimeoutError("timed out"),
    ],
)
def test_transient_errors(error: BaseException):
    assert is_transient_error(error)


@pytest.mark.parametrize(
    "error",
    [
        ApiError(status=404, subStatus="0", userMessage="not found"),
        ApiError(status=401, subStatus="0", userMessage="unauthorized"),
        # a broken body is reported with the status of the response
        ApiError(status=200, subStatus="0", userMessage="invalid json"),
        ValueError("template error"),
    ],
)
def test_permanent_errors(error: BaseException):
    assert not is_transient_error(error)


def test_rate_limited_track_is_reported_as_transient():
    report = DownloadReport()
    report.add_failure(kind="album", name="Album: Foo, ID: 1", error=RateLimitError())

    assert report.has_transient_failures
    assert len(report.transient_failures) == 1
    assert not report.permanent_skips

    (line,) = report.summary_lines()
    assert "1 album" in line
    assert "temporary" in line


def test_unavailable_track_is_not_transient():
    report = DownloadReport()
    report.add_skip(
        kind="track", name="Foo (ID: 1)", reason="streaming not allowed"
    )

    assert not report.has_transient_failures
    assert len(report.permanent_skips) == 1

    (line,) = report.summary_lines()
    assert "1 track" in line
    assert "not available" in line


def test_empty_report_has_no_summary():
    assert DownloadReport().summary_lines() == []
    assert not DownloadReport().has_transient_failures


def test_both_kinds_of_failure_are_reported_separately():
    report = DownloadReport()
    report.add_failure(kind="album", name="Album: Foo, ID: 1", error=RateLimitError())
    report.add_skip(kind="track", name="Bar (ID: 2)", reason="streaming not allowed")

    assert len(report.summary_lines()) == 2
    assert report.has_transient_failures


def test_count_kinds_groups_and_pluralizes():
    report = DownloadReport()

    for album_id in (1, 2):
        report.add_failure(
            kind="album", name=f"Album: ID {album_id}", error=RateLimitError()
        )

    report.add_failure(kind="track", name="Track: ID 3", error=RateLimitError())

    assert count_kinds(report.transient_failures) == "2 albums, 1 track"


def test_existing_m3u_is_kept_after_a_partial_run(tmp_path: Path):
    m3u_path = tmp_path / "playlist.m3u"
    m3u_path.write_text("#EXTM3U\n")

    report = DownloadReport()
    report.add_failure(kind="album", name="Album: Foo, ID: 1", error=RateLimitError())

    assert keep_existing_m3u(m3u_path, report)


def test_m3u_is_written_when_only_unavailable_items_were_skipped(tmp_path: Path):
    m3u_path = tmp_path / "playlist.m3u"
    m3u_path.write_text("#EXTM3U\n")

    report = DownloadReport()
    report.add_skip(kind="track", name="Foo (ID: 1)", reason="streaming not allowed")

    assert not keep_existing_m3u(m3u_path, report)


def test_m3u_is_written_when_it_does_not_exist_yet(tmp_path: Path):
    report = DownloadReport()
    report.add_failure(kind="album", name="Album: Foo, ID: 1", error=RateLimitError())

    assert not keep_existing_m3u(tmp_path / "playlist.m3u", report)
