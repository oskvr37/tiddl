from typing import Any
import pytest
from pytest_mock import MockerFixture
from tiddl.core.auth.api import AuthAPI
from tiddl.core.auth.models import (
    AuthDeviceResponse,
    AuthResponseWithRefresh,
    AuthResponse,
)


@pytest.fixture
def mock_auth_client(mocker: MockerFixture) -> Any:
    client = mocker.Mock()

    client.get_device_auth.return_value = {
        "deviceCode": "abc",
        "userCode": "123",
        "verificationUri": "https://verify",
        "verificationUriComplete": "https://verify?code=123",
        "expiresIn": 300,
        "interval": 5,
    }

    user_data: dict[str, Any] = {
        "userId": 1,
        "email": "test@example.com",
        "countryCode": "US",
        "fullName": None,
        "firstName": None,
        "lastName": None,
        "nickname": None,
        "username": "tester",
        "address": None,
        "city": None,
        "postalcode": None,
        "usState": None,
        "phoneNumber": None,
        "birthday": None,
        "channelId": 0,
        "parentId": 0,
        "acceptedEULA": True,
        "created": 0,
        "updated": 0,
        "facebookUid": 0,
        "appleUid": None,
        "googleUid": None,
        "accountLinkCreated": True,
        "emailVerified": True,
        "newUser": True,
    }

    auth_base: dict[str, Any] = {
        "access_token": "token123",
        "refresh_token": "refresh123",
        "expires_in": 3600,
        "user_id": 1,
        "scope": "r_usr",
        "clientName": "tidal",
        "token_type": "Bearer",
        "user": user_data,
    }

    client.get_auth.return_value = auth_base.copy()
    client.refresh_token.return_value = auth_base.copy()
    client.logout_token.return_value = None

    return client


def test_get_device_auth_returns_model(mock_auth_client: Any) -> None:
    api: AuthAPI = AuthAPI(client=mock_auth_client)
    result: AuthDeviceResponse = api.get_device_auth()

    mock_auth_client.get_device_auth.assert_called_once()
    assert isinstance(result, AuthDeviceResponse)
    assert result.deviceCode == "abc"
    assert result.interval == 5


def test_get_auth_returns_model(mock_auth_client: Any) -> None:
    api: AuthAPI = AuthAPI(client=mock_auth_client)
    result: AuthResponseWithRefresh = api.get_auth("device123")

    mock_auth_client.get_auth.assert_called_once_with("device123")
    assert isinstance(result, AuthResponseWithRefresh)
    assert result.access_token == "token123"
    assert result.refresh_token == "refresh123"
    assert result.user.userId == 1


def test_refresh_token_returns_model(mock_auth_client: Any) -> None:
    api: AuthAPI = AuthAPI(client=mock_auth_client)
    result: AuthResponse = api.refresh_token("refresh123")

    mock_auth_client.refresh_token.assert_called_once_with("refresh123")
    assert isinstance(result, AuthResponse)
    assert result.access_token == "token123"


def test_logout_token_calls_client(mock_auth_client: Any) -> None:
    api: AuthAPI = AuthAPI(client=mock_auth_client)
    api.logout_token("token123")

    mock_auth_client.logout_token.assert_called_once_with("token123")
