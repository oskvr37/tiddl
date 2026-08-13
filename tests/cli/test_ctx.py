from pathlib import Path

from pytest_mock import MockerFixture
from rich.console import Console

from tiddl.cli.ctx import ContextObject
from tiddl.cli.utils.auth.models import AuthData
from tiddl.core.auth.profiles import ProfileToken


def test_playback_api_uses_derived_token_and_persists_rotation(
    mocker: MockerFixture,
):
    initial_auth_data = AuthData(
        token="catalog-token",
        refresh_token="refresh-token",
        expires_at=3600,
        user_id="1",
        country_code="US",
    )
    latest_auth_data = initial_auth_data.model_copy()
    mocker.patch(
        "tiddl.cli.ctx.load_auth_data",
        side_effect=[initial_auth_data, latest_auth_data],
    )
    save_auth_data = mocker.patch("tiddl.cli.ctx.save_auth_data")

    token_manager = mocker.Mock()
    token_manager.get_token.return_value = ProfileToken(
        access_token="profile-access-token",
        client_id="profile-client-id",
        expires_at=3600,
    )
    token_manager_class = mocker.patch(
        "tiddl.cli.ctx.ProfileTokenManager", return_value=token_manager
    )
    tidal_client = mocker.Mock()
    tidal_client_class = mocker.patch(
        "tiddl.cli.ctx.TidalClient", return_value=tidal_client
    )

    context = ContextObject(
        api_omit_cache=True,
        debug_path=Path("/tmp/debug"),
        console=Console(),
    )
    api = context.get_playback_api("hires")

    assert api.client is tidal_client
    token_manager.get_token.assert_called_once_with("hires")
    tidal_client_class.assert_called_once_with(
        token="profile-access-token",
        client_id="profile-client-id",
        cache_name=mocker.ANY,
        omit_cache=True,
        debug_path=Path("/tmp/debug"),
        on_token_expiry=mocker.ANY,
    )

    on_refresh_token = token_manager_class.call_args.kwargs["on_refresh_token"]
    on_refresh_token("rotated-refresh-token")

    assert latest_auth_data.refresh_token == "rotated-refresh-token"
    save_auth_data.assert_called_once_with(auth_data=latest_auth_data)


def test_playback_api_reuses_api_and_updates_its_access_token(
    mocker: MockerFixture,
):
    auth_data = AuthData(
        refresh_token="refresh-token",
        user_id="1",
        country_code="US",
    )
    load_auth_data = mocker.patch(
        "tiddl.cli.ctx.load_auth_data", return_value=auth_data
    )
    token_manager = mocker.Mock()
    token_manager.get_token.side_effect = [
        ProfileToken("first-token", "client-id", 3600),
        ProfileToken("second-token", "client-id", 7200),
    ]
    mocker.patch("tiddl.cli.ctx.ProfileTokenManager", return_value=token_manager)
    tidal_client = mocker.Mock()
    tidal_client_class = mocker.patch(
        "tiddl.cli.ctx.TidalClient", return_value=tidal_client
    )
    context = ContextObject(False, None, Console())

    first = context.get_playback_api("atmos")
    second = context.get_playback_api("atmos")

    assert first is second
    assert tidal_client.token == "second-token"
    tidal_client_class.assert_called_once()
    load_auth_data.assert_called_once()


def test_catalog_refresh_keeps_profile_manager_synchronized(
    mocker: MockerFixture,
):
    initial_auth_data = AuthData(
        token="expired-token",
        refresh_token="original-refresh-token",
        user_id="1",
        country_code="US",
    )
    latest_auth_data = initial_auth_data.model_copy()
    mocker.patch(
        "tiddl.cli.ctx.load_auth_data",
        side_effect=[initial_auth_data, latest_auth_data],
    )
    mocker.patch("tiddl.cli.ctx.time", return_value=1000)
    save_auth_data = mocker.patch("tiddl.cli.ctx.save_auth_data")
    tidal_client_class = mocker.patch("tiddl.cli.ctx.TidalClient")
    token_manager = mocker.Mock()
    context = ContextObject(False, None, Console())
    context._profile_token_manager = token_manager
    context.auth_api.refresh_token = mocker.Mock(
        return_value=mocker.Mock(
            access_token="new-access-token",
            expires_in=3600,
            refresh_token="rotated-refresh-token",
        )
    )

    _ = context.api
    on_token_expiry = tidal_client_class.call_args.kwargs["on_token_expiry"]

    assert on_token_expiry() == "new-access-token"
    token_manager.replace_refresh_token.assert_called_once_with("rotated-refresh-token")
    assert latest_auth_data.token == "new-access-token"
    assert latest_auth_data.expires_at == 4600
    assert latest_auth_data.refresh_token == "rotated-refresh-token"
    save_auth_data.assert_called_once_with(auth_data=latest_auth_data)
