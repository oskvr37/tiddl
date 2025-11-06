import pytest
from typing import Any
from tiddl.core.auth.exceptions import AuthClientError


def test_auth_client_error_attributes():
    data: dict[str, Any] = {
        "status": 1,
        "error": "error",
        "sub_status": "sub_status",
        "error_description": "error_description",
    }

    e = AuthClientError(**data)

    assert isinstance(e, Exception)
    assert e.status == data["status"]
    assert e.error == data["error"]
    assert e.sub_status == data["sub_status"]
    assert e.error_description == data["error_description"]


def test_auth_client_error_raises():
    with pytest.raises(AuthClientError) as exc:
        raise AuthClientError(400, "bad_request", "invalid", "Malformed input")

    assert exc.value.status == 400
    assert exc.value.error == "bad_request"


def test_auth_client_error_string():
    data: dict[str, Any] = {
        "status": 1,
        "error": "error",
        "sub_status": "sub_status",
        "error_description": "error_description",
    }

    e = AuthClientError(**data)

    assert str(e) == f"{e.error}, {e.error_description}, {e.status}/{e.sub_status}"
