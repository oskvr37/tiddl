import pytest
from typing import Any
from tiddl.core.api.exceptions import ApiError


def test_api_error_attributes():
    data: dict[str, Any] = {
        "status": 1,
        "subStatus": "sub_status",
        "userMessage": "user_message",
    }

    e = ApiError(**data)

    assert isinstance(e, Exception)
    assert e.status == data["status"]
    assert e.sub_status == data["subStatus"]
    assert e.user_message == data["userMessage"]


def test_api_error_raises():
    with pytest.raises(ApiError) as exc:
        raise ApiError(400, "bad_request", "invalid")

    assert exc.value.status == 400
    assert exc.value.sub_status == "bad_request"


def test_api_error_string():
    data: dict[str, Any] = {
        "status": 1,
        "subStatus": "sub_status",
        "userMessage": "user_message",
    }

    e = ApiError(**data)

    assert str(e) == f"{e.user_message}, {e.status}/{e.sub_status}"
