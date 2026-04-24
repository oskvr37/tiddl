from pathlib import Path

import pytest

from tiddl.cli.utils.path import resolve_existing_path_case


def test_resolve_existing_path_case_reuses_existing_directories(tmp_path: Path):
    existing_album = tmp_path / "FooBar" / "[2024.01.02] Album"
    existing_album.mkdir(parents=True)

    path = resolve_existing_path_case(
        tmp_path,
        Path("foobar") / "[2024.01.02] album" / "01 - Track.flac",
    )

    assert path == existing_album / "01 - Track.flac"


def test_resolve_existing_path_case_reuses_existing_file(tmp_path: Path):
    existing_file = tmp_path / "FooBar" / "01 - Track.flac"
    existing_file.parent.mkdir()
    existing_file.touch()

    path = resolve_existing_path_case(tmp_path, Path("foobar") / "01 - track.flac")

    assert path == existing_file


def test_resolve_existing_path_case_keeps_new_components(tmp_path: Path):
    path = resolve_existing_path_case(tmp_path, Path("FooBar") / "New Album")

    assert path == tmp_path / "FooBar" / "New Album"


def test_resolve_existing_path_case_rejects_absolute_path(tmp_path: Path):
    with pytest.raises(ValueError, match="relative_path"):
        resolve_existing_path_case(tmp_path, tmp_path / "FooBar")
