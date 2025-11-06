import pytest
from unittest.mock import patch, MagicMock
from time import time
from typer.testing import CliRunner

from tiddl.core.auth import AuthClientError
from tiddl.cli.commands.auth import auth_command
from tiddl.cli.utils.auth import AuthData

runner = CliRunner()


def test_login_already_logged(monkeypatch: pytest.MonkeyPatch):
    """Should exit early if user is logged in."""

    monkeypatch.setattr(
        "tiddl.cli.commands.auth.load_auth_data", lambda: AuthData(token="token")
    )

    result = runner.invoke(auth_command, ["login"])

    assert "Already logged in." in result.stdout
    assert result.exit_code == 0


def test_login_success(monkeypatch: pytest.MonkeyPatch):
    """Should save user token."""

    monkeypatch.setattr(
        "tiddl.cli.commands.auth.load_auth_data", lambda: AuthData(token=None)
    )

    device_auth_mock = MagicMock()
    device_auth_mock.verificationUriComplete = "verify.uri"
    device_auth_mock.deviceCode = "device123"
    device_auth_mock.expiresIn = 60
    device_auth_mock.interval = 1

    auth_mock = MagicMock()
    auth_mock.access_token = "newtoken"
    auth_mock.refresh_token = "refreshtoken"
    auth_mock.expires_in = 3600
    auth_mock.user_id = 123
    auth_mock.user.countryCode = "US"

    with (
        patch("tiddl.cli.commands.auth.AuthAPI") as MockAuthAPI,
        patch("tiddl.cli.commands.auth.typer.launch") as mock_launch,
        patch("tiddl.cli.commands.auth.save_auth_data") as mock_save,
        patch("tiddl.cli.commands.auth.time", side_effect=lambda: 1000),
        patch("tiddl.cli.commands.auth.sleep"),
    ):

        auth_api = MockAuthAPI.return_value
        auth_api.get_device_auth.return_value = device_auth_mock
        auth_api.get_auth.side_effect = [
            AuthClientError(error="authorization_pending"),
            auth_mock,
        ]

        result = runner.invoke(auth_command, ["login"])

        auth_api.get_device_auth.assert_called_once()
        auth_api.get_auth.assert_called()
        mock_launch.assert_called_once_with("https://verify.uri")
        mock_save.assert_called_once()
        saved_data = mock_save.call_args[0][0]
        assert saved_data.token == "newtoken"
        assert "Logged in!" in result.stdout
        assert result.exit_code == 0


def test_login_expired(monkeypatch: pytest.MonkeyPatch):
    """Should not save token and exit."""

    monkeypatch.setattr(
        "tiddl.cli.commands.auth.load_auth_data", lambda: AuthData(token=None)
    )

    device_auth_mock = MagicMock()
    device_auth_mock.verificationUriComplete = "verify.uri"
    device_auth_mock.deviceCode = "device123"
    device_auth_mock.expiresIn = 60
    device_auth_mock.interval = 1

    with (
        patch("tiddl.cli.commands.auth.AuthAPI") as MockAuthAPI,
        patch("tiddl.cli.commands.auth.typer.launch") as mock_launch,
        patch("tiddl.cli.commands.auth.save_auth_data") as mock_save,
        patch("tiddl.cli.commands.auth.time", side_effect=lambda: 1000),
        patch("tiddl.cli.commands.auth.sleep"),
    ):

        auth_api = MockAuthAPI.return_value
        auth_api.get_device_auth.return_value = device_auth_mock
        auth_api.get_auth.side_effect = [
            AuthClientError(error="expired_token"),
        ]

        result = runner.invoke(auth_command, ["login"])

        auth_api.get_device_auth.assert_called_once()
        auth_api.get_auth.assert_called()
        mock_launch.assert_called_once_with("https://verify.uri")
        mock_save.assert_not_called()
        assert "Time for authentication has expired." in result.stdout
        assert result.exit_code == 0


def test_logout_with_token(monkeypatch: pytest.MonkeyPatch):
    """Should clear auth data and logout token in API."""

    monkeypatch.setattr(
        "tiddl.cli.commands.auth.load_auth_data", lambda: AuthData(token="token")
    )

    with (
        patch("tiddl.cli.commands.auth.AuthAPI") as MockAuthAPI,
        patch("tiddl.cli.commands.auth.save_auth_data") as mock_save,
    ):
        mock_api_instance = MockAuthAPI.return_value
        result = runner.invoke(auth_command, ["logout"])

        mock_api_instance.logout_token.assert_called_once_with("token")
        mock_save.assert_called_once_with(AuthData())

        assert "Logged out!" in result.stdout
        assert result.exit_code == 0


def test_logout_no_token(monkeypatch: pytest.MonkeyPatch):
    """Should only clear auth data."""

    monkeypatch.setattr(
        "tiddl.cli.commands.auth.load_auth_data", lambda: AuthData(token=None)
    )

    with (
        patch("tiddl.cli.commands.auth.AuthAPI") as MockAuthAPI,
        patch("tiddl.cli.commands.auth.save_auth_data") as mock_save,
    ):
        result = runner.invoke(auth_command, ["logout"])

        mock_save.assert_called_once_with(AuthData())
        MockAuthAPI.assert_not_called()

        assert "Logged out!" in result.stdout
        assert result.exit_code == 0


def test_refresh_not_logged_in(monkeypatch: pytest.MonkeyPatch):
    """Should exit early if refresh_token is missing."""

    monkeypatch.setattr(
        "tiddl.cli.commands.auth.load_auth_data", lambda: AuthData(refresh_token=None)
    )
    result = runner.invoke(auth_command, ["refresh"])

    assert "Not logged in." in result.stdout
    assert result.exit_code == 0


def test_refresh_not_expired(monkeypatch: pytest.MonkeyPatch):
    """Should exit early if token still valid."""

    monkeypatch.setattr(
        "tiddl.cli.commands.auth.load_auth_data",
        lambda: AuthData(
            token="abc", refresh_token="ref", expires_at=int(time()) + 3600
        ),
    )
    result = runner.invoke(auth_command, ["refresh"])

    assert "Auth token expires in" in result.stdout
    assert result.exit_code == 0


def test_refresh_success(monkeypatch: pytest.MonkeyPatch):
    """Should refresh token if expired."""

    expired_data = AuthData(
        token="oldtoken", refresh_token="refreshtoken", expires_at=0
    )
    monkeypatch.setattr("tiddl.cli.commands.auth.load_auth_data", lambda: expired_data)

    mock_auth_response = MagicMock()
    mock_auth_response.access_token = "newtoken"

    with (
        patch("tiddl.cli.commands.auth.AuthAPI") as MockAuthAPI,
        patch("tiddl.cli.commands.auth.save_auth_data") as mock_save,
    ):

        MockAuthAPI.return_value.refresh_token.return_value = mock_auth_response

        result = runner.invoke(auth_command, ["refresh"])

        mock_save.assert_called_once_with(expired_data)
        assert "Auth token has been refreshed!" in result.stdout
        assert result.exit_code == 0
