import pytest
from pytest_mock import MockerFixture

from tiddl.core.auth.client import CLIENT_ID, CLIENT_SECRET
from tiddl.core.auth.profiles import (
    CLIENT_PROFILES,
    ClientProfile,
    ProfileTokenManager,
    select_playback_profile,
)


def test_atmos_profile_uses_configured_auth_credentials():
    assert CLIENT_PROFILES["atmos"].client_id == CLIENT_ID
    assert CLIENT_PROFILES["atmos"].client_secret == CLIENT_SECRET


@pytest.mark.parametrize(
    ("atmos_filter", "atmos_available", "expected"),
    [
        ("none", True, "hires"),
        ("only", False, "atmos"),
        ("allow", True, "atmos"),
        ("allow", False, "hires"),
    ],
)
def test_select_playback_profile(atmos_filter, atmos_available, expected):
    assert select_playback_profile(atmos_filter, atmos_available) == expected


@pytest.mark.parametrize("profile_name", ["hires", "atmos"])
def test_manager_builds_auth_client_for_profile(mocker: MockerFixture, profile_name):
    auth_client_class = mocker.patch("tiddl.core.auth.profiles.AuthClient")
    auth_client_class.return_value.refresh_token.return_value = {
        "access_token": "access-token",
        "expires_in": 3600,
    }

    ProfileTokenManager("refresh-token").get_token(profile_name)

    profile = CLIENT_PROFILES[profile_name]
    auth_client_class.assert_called_once_with(
        client_id=profile.client_id,
        client_secret=profile.client_secret,
        refresh_with_basic_auth=profile.refresh_with_basic_auth,
        refresh_scope="r_usr+w_usr",
    )


def test_profiles_use_one_refresh_token(mocker: MockerFixture):
    refresh_calls: list[tuple[str, str]] = []

    def client_factory(profile: ClientProfile):
        client = mocker.Mock()

        def refresh_token(refresh_token: str):
            refresh_calls.append((profile.client_id, refresh_token))
            return {
                "access_token": f"access-{profile.client_id}",
                "expires_in": 3600,
            }

        client.refresh_token.side_effect = refresh_token
        return client

    manager = ProfileTokenManager(
        refresh_token="one-refresh-token",
        client_factory=client_factory,
    )

    hires = manager.get_token("hires")
    atmos = manager.get_token("atmos")

    assert hires.client_id == CLIENT_PROFILES["hires"].client_id
    assert atmos.client_id == CLIENT_PROFILES["atmos"].client_id
    assert refresh_calls == [
        (CLIENT_PROFILES["hires"].client_id, "one-refresh-token"),
        (CLIENT_PROFILES["atmos"].client_id, "one-refresh-token"),
    ]


def test_profile_tokens_are_cached_until_the_expiry_margin(
    mocker: MockerFixture,
):
    now = [0.0]
    client = mocker.Mock()
    client.refresh_token.side_effect = [
        {"access_token": "first", "expires_in": 100},
        {"access_token": "second", "expires_in": 100},
    ]
    factory = mocker.Mock(return_value=client)
    manager = ProfileTokenManager(
        refresh_token="refresh-token",
        clock=lambda: now[0],
        expiry_margin=10,
        client_factory=factory,
    )

    first = manager.get_token("hires")
    now[0] = 89
    cached = manager.get_token("hires")
    now[0] = 90
    refreshed = manager.get_token("hires")

    assert first is cached
    assert refreshed.access_token == "second"
    assert client.refresh_token.call_count == 2


def test_profile_token_can_be_force_refreshed(mocker: MockerFixture):
    client = mocker.Mock()
    client.refresh_token.side_effect = [
        {"access_token": "first", "expires_in": 3600},
        {"access_token": "second", "expires_in": 3600},
    ]
    manager = ProfileTokenManager(
        refresh_token="refresh-token",
        client_factory=mocker.Mock(return_value=client),
    )

    manager.get_token("atmos")
    refreshed = manager.get_token("atmos", force=True)

    assert refreshed.access_token == "second"
    assert client.refresh_token.call_count == 2


def test_rotated_refresh_token_is_saved_and_reused(mocker: MockerFixture):
    refresh_calls: list[str] = []
    on_refresh_token = mocker.Mock()

    def client_factory(profile: ClientProfile):
        client = mocker.Mock()

        def refresh_token(refresh_token: str):
            refresh_calls.append(refresh_token)
            response = {
                "access_token": f"access-{profile.client_id}",
                "expires_in": 3600,
            }
            if len(refresh_calls) == 1:
                response["refresh_token"] = "rotated-refresh-token"
            return response

        client.refresh_token.side_effect = refresh_token
        return client

    manager = ProfileTokenManager(
        refresh_token="original-refresh-token",
        on_refresh_token=on_refresh_token,
        client_factory=client_factory,
    )

    manager.get_token("hires")
    manager.get_token("atmos")

    assert refresh_calls == [
        "original-refresh-token",
        "rotated-refresh-token",
    ]
    on_refresh_token.assert_called_once_with("rotated-refresh-token")


def test_replace_refresh_token_uses_external_rotation(mocker: MockerFixture):
    client = mocker.Mock()
    client.refresh_token.return_value = {
        "access_token": "access-token",
        "expires_in": 3600,
    }
    manager = ProfileTokenManager(
        refresh_token="original-refresh-token",
        client_factory=mocker.Mock(return_value=client),
    )

    manager.replace_refresh_token("external-refresh-token")
    manager.get_token("hires")

    client.refresh_token.assert_called_once_with("external-refresh-token")
