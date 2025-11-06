import pytest
from pytest_mock import MockerFixture
from tiddl.core.auth.client import AuthClient
from tiddl.core.auth.exceptions import AuthClientError


def test_get_device_auth_calls_request(mocker: MockerFixture):
    mock_request = mocker.patch("tiddl.core.auth.client.request")

    data = {"device_code": "abc"}
    mock_response = mocker.Mock()
    mock_response.json.return_value = data
    mock_request.return_value = mock_response

    client = AuthClient()
    result = client.get_device_auth()

    mock_request.assert_called_once_with(
        "POST",
        "https://auth.tidal.com/v1/oauth2/device_authorization",
        data={"client_id": client.client_id, "scope": "r_usr+w_usr+w_sub"},
    )

    assert result == data


def test_get_auth_returns_json_on_200(mocker: MockerFixture):
    mock_request = mocker.patch("tiddl.core.auth.client.request")
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "token123",
        "refresh_token": "refresh123",
        "expires_in": 3600,
    }
    mock_request.return_value = mock_response

    client = AuthClient()
    result = client.get_auth("device123")

    assert result["access_token"] == "token123"
    assert result["refresh_token"] == "refresh123"
    assert result["expires_in"] == 3600

    mock_request.assert_called_once_with(
        "POST",
        "https://auth.tidal.com/v1/oauth2/token",
        data={
            "client_id": client.client_id,
            "device_code": "device123",
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "scope": "r_usr+w_usr+w_sub",
        },
        auth=(client.client_id, client.client_secret),
    )


def test_get_auth_raises_on_non_200(mocker: MockerFixture):
    mock_request = mocker.patch("tiddl.core.auth.client.request")
    mock_response = mocker.Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "error": "error",
        "status": 400,
        "sub_status": 1001,
        "error_description": "invalid",
    }
    mock_request.return_value = mock_response

    client = AuthClient()

    with pytest.raises(AuthClientError):
        client.get_auth("device123")

    mock_request.assert_called_once_with(
        "POST",
        "https://auth.tidal.com/v1/oauth2/token",
        data={
            "client_id": client.client_id,
            "device_code": "device123",
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "scope": "r_usr+w_usr+w_sub",
        },
        auth=(client.client_id, client.client_secret),
    )


def test_refresh_token(mocker: MockerFixture):
    mock_request = mocker.patch("tiddl.core.auth.client.request")

    mock_response = mocker.Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "token": "abc",
    }
    mock_request.return_value = mock_response

    refresh_token = "token"

    client = AuthClient()
    result = client.refresh_token(refresh_token)

    mock_request.assert_called_once_with(
        "POST",
        "https://auth.tidal.com/v1/oauth2/token",
        data={
            "client_id": client.client_id,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": "r_usr+w_usr+w_sub",
        },
        auth=(client.client_id, client.client_secret),
    )

    assert result["token"] == "abc"


def test_logout_token(mocker: MockerFixture):
    mock_request = mocker.patch("tiddl.core.auth.client.request")

    client = AuthClient()
    client.logout_token("token")

    mock_request.assert_called_once_with(
        "POST",
        "https://api.tidal.com/v1/logout",
        headers={"authorization": "Bearer token"},
    )
