from dataclasses import dataclass
from pathlib import Path

import aiohttp
from requests import exceptions as requests_exceptions

from tiddl.core.api import ApiError

# exit code used when items were skipped because of temporary errors
EXIT_PARTIAL = 2

TRANSIENT_EXCEPTIONS = (
    requests_exceptions.ConnectionError,
    requests_exceptions.Timeout,
    aiohttp.ClientConnectionError,
    aiohttp.ServerTimeoutError,
    TimeoutError,
)


def is_transient_error(error: BaseException) -> bool:
    """
    Whether a failure is expected to resolve itself on a later run.

    Rate limits and network errors are transient, a resource that is not
    available for streaming or does not exist is not.
    """

    if isinstance(error, ApiError):
        return error.is_transient

    return isinstance(error, TRANSIENT_EXCEPTIONS)


def keep_existing_m3u(m3u_path: Path, report: "DownloadReport") -> bool:
    """
    Whether an already existing m3u file should be left alone.

    A run that lost items to temporary errors writes a shorter playlist,
    which would overwrite a complete one from an earlier run.
    """

    return report.has_transient_failures and m3u_path.exists()


@dataclass
class SkippedResource:
    kind: str
    """`track`, `album`, `playlist`, ..."""
    name: str
    reason: str
    transient: bool


def count_kinds(resources: list[SkippedResource]) -> str:
    """`2 albums, 1 track`"""

    counts: dict[str, int] = {}

    for resource in resources:
        counts[resource.kind] = counts.get(resource.kind, 0) + 1

    return ", ".join(
        f"{count} {kind}{'' if count == 1 else 's'}"
        for kind, count in sorted(counts.items())
    )


class DownloadReport:
    """
    Keeps track of resources that did not end up being downloaded,
    so a partial run can be reported instead of silently losing items.
    """

    skipped: list[SkippedResource]

    def __init__(self) -> None:
        self.skipped = []

    def add_failure(self, kind: str, name: str, error: BaseException) -> None:
        """Record a resource that failed with an exception."""

        self.skipped.append(
            SkippedResource(
                kind=kind,
                name=name,
                reason=str(error) or error.__class__.__name__,
                transient=is_transient_error(error),
            )
        )

    def add_skip(self, kind: str, name: str, reason: str) -> None:
        """Record a resource that is permanently unavailable."""

        self.skipped.append(
            SkippedResource(kind=kind, name=name, reason=reason, transient=False)
        )

    @property
    def transient_failures(self) -> list[SkippedResource]:
        return [resource for resource in self.skipped if resource.transient]

    @property
    def permanent_skips(self) -> list[SkippedResource]:
        return [resource for resource in self.skipped if not resource.transient]

    @property
    def has_transient_failures(self) -> bool:
        return any(resource.transient for resource in self.skipped)

    def summary_lines(self) -> list[str]:
        """Lines to print after a download, with rich markup."""

        lines: list[str] = []

        if self.transient_failures:
            lines.append(
                f"[yellow]Incomplete:[/] {count_kinds(self.transient_failures)} "
                "skipped due to temporary errors (rate limit or network), "
                "they should succeed on another run"
            )

        if self.permanent_skips:
            lines.append(
                f"Skipped {count_kinds(self.permanent_skips)} "
                "that are not available"
            )

        return lines
