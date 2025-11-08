import pytest
from pathlib import Path

from tiddl.cli.const import get_app_path, APP_DIR_NAME, ENV_KEY


def test_env_key_overrides(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    custom_path = tmp_path / "customdir"
    monkeypatch.setenv(ENV_KEY, str(custom_path))
    app_path = get_app_path(ENV_KEY)

    assert app_path == custom_path


def test_default_path_if_unset(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(ENV_KEY, raising=False)
    app_path = get_app_path(ENV_KEY)

    assert str(Path.home()) in str(app_path)
    assert app_path.name == APP_DIR_NAME
