import pytest
import json

from pydantic import BaseModel
from pytest_mock import MockerFixture
from pathlib import Path
from requests.exceptions import JSONDecodeError

from tiddl.core.api.client import TidalClient, ApiError, RateLimitError


def test_tidal_client_init(mocker: MockerFixture):
    mock_cached_session = mocker.patch("tiddl.core.api.client.CachedSession")
    mock_session = mock_cached_session.return_value

    client = TidalClient(
        token="test-token",
        cache_name="test_cache",
        omit_cache=True,
        debug_path=Path("/tmp/debug"),
    )

    mock_cached_session.assert_called_once_with(
        cache_name="test_cache", always_revalidate=True
    )

    assert client.token == "test-token"
    assert client.debug_path == Path("/tmp/debug")
    assert client.session is mock_session
    assert mock_session.headers["Authorization"] == "Bearer test-token"
    assert mock_session.headers["Accept"] == "application/json"


@pytest.mark.parametrize("omit_cache", [True, False])
def test_omit_cache_flag(mocker: MockerFixture, omit_cache: bool):
    mock_cached_session = mocker.patch("tiddl.core.api.client.CachedSession")
    TidalClient("token", "cache", omit_cache=omit_cache)
    mock_cached_session.assert_called_once_with(
        cache_name="cache", always_revalidate=omit_cache
    )


class DummyModel(BaseModel):
    foo: str


def test_fetch_success(mocker: MockerFixture, tmp_path: Path):
    mock_session = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.from_cache = False
    mock_response.json.return_value = {"foo": "bar"}
    mock_session.get.return_value = mock_response

    mocker.patch("tiddl.core.api.client.API_URL", "https://api.test")
    client = TidalClient("token", tmp_path / "cache", debug_path=tmp_path)
    client.session = mock_session

    result = client.fetch(DummyModel, "albums/123", {"limit": 10}, expire_after=999)
    assert result.foo == "bar"

    mock_session.get.assert_called_once_with(
        "https://api.test/albums/123",
        params={"limit": 10},
        expire_after=999,
    )

    debug_file = tmp_path / "albums/123.json"
    assert debug_file.exists()

    content = json.loads(debug_file.read_text())
    assert content["status_code"] == 200
    assert content["endpoint"] == "albums/123"
    assert content["params"]["limit"] == 10
    assert content["data"]["foo"] == "bar"


def test_fetch_error_raises_api_error(mocker: MockerFixture, tmp_path: Path):
    mock_session = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.status_code = 400
    mock_response.from_cache = False
    mock_response.json.return_value = {
        "status": 400,
        "subStatus": "Bad request",
        "userMessage": "user_message",
    }
    mock_session.get.return_value = mock_response

    client = TidalClient("token", tmp_path / "cache")
    client.session = mock_session

    with pytest.raises(ApiError):
        client.fetch(DummyModel, "bad/endpoint")


def build_response(
    mocker: MockerFixture,
    status_code: int,
    json_data: dict | None = None,
    headers: dict[str, str] = {},
    from_cache: bool = False,
):
    response = mocker.Mock()
    response.status_code = status_code
    response.from_cache = from_cache
    response.headers = dict(headers)

    if json_data is None:
        response.json.side_effect = JSONDecodeError("no json", "", 0)
    else:
        response.json.return_value = json_data

    return response


def test_fetch_retries_rate_limited_request(mocker: MockerFixture, tmp_path: Path):
    mock_sleep = mocker.patch("tiddl.core.api.client.sleep")

    mock_session = mocker.Mock()
    mock_session.get.side_effect = [
        build_response(mocker, 429),
        build_response(mocker, 200, {"foo": "bar"}),
    ]

    client = TidalClient("token", tmp_path / "cache", min_request_interval=0)
    client.session = mock_session

    assert client.fetch(DummyModel, "albums/123").foo == "bar"

    assert mock_session.get.call_count == 2
    mock_sleep.assert_called_once()

    # first backoff is jittered within [RETRY_DELAY / 2, RETRY_DELAY]
    (delay,) = mock_sleep.call_args.args
    assert 1 <= delay <= 2


def test_fetch_gives_up_on_permanent_rate_limit(mocker: MockerFixture, tmp_path: Path):
    mocker.patch("tiddl.core.api.client.sleep")

    mock_session = mocker.Mock()
    mock_session.get.return_value = build_response(mocker, 429)

    client = TidalClient(
        "token",
        tmp_path / "cache",
        min_request_interval=0,
        rate_limit_max_retries=3,
    )
    client.session = mock_session

    with pytest.raises(RateLimitError) as exc_info:
        client.fetch(DummyModel, "albums/123")

    assert exc_info.value.status == 429
    assert exc_info.value.is_transient
    assert mock_session.get.call_count == 3


def test_fetch_honors_retry_after_header(mocker: MockerFixture, tmp_path: Path):
    mock_sleep = mocker.patch("tiddl.core.api.client.sleep")

    mock_session = mocker.Mock()
    mock_session.get.side_effect = [
        build_response(mocker, 429, headers={"Retry-After": "30"}),
        build_response(mocker, 200, {"foo": "bar"}),
    ]

    client = TidalClient("token", tmp_path / "cache", min_request_interval=0)
    client.session = mock_session

    client.fetch(DummyModel, "albums/123")

    mock_sleep.assert_called_once_with(30.0)


def test_fetch_caps_retry_after_header(mocker: MockerFixture, tmp_path: Path):
    mock_sleep = mocker.patch("tiddl.core.api.client.sleep")

    mock_session = mocker.Mock()
    mock_session.get.side_effect = [
        build_response(mocker, 429, headers={"Retry-After": "600"}),
        build_response(mocker, 200, {"foo": "bar"}),
    ]

    client = TidalClient(
        "token",
        tmp_path / "cache",
        min_request_interval=0,
        rate_limit_max_backoff=10,
    )
    client.session = mock_session

    client.fetch(DummyModel, "albums/123")

    mock_sleep.assert_called_once_with(10)


def test_fetch_broken_body_is_not_treated_as_rate_limit(
    mocker: MockerFixture, tmp_path: Path
):
    mocker.patch("tiddl.core.api.client.sleep")

    mock_session = mocker.Mock()
    mock_session.get.return_value = build_response(mocker, 200)

    client = TidalClient("token", tmp_path / "cache", min_request_interval=0)
    client.session = mock_session

    with pytest.raises(ApiError) as exc_info:
        client.fetch(DummyModel, "albums/123")

    assert not isinstance(exc_info.value, RateLimitError)
    assert exc_info.value.status == 200
    assert not exc_info.value.is_transient
    assert "json" in exc_info.value.user_message.lower()


def test_fetch_throttles_requests_that_reach_the_api(
    mocker: MockerFixture, tmp_path: Path
):
    mock_sleep = mocker.patch("tiddl.core.api.client.sleep")
    # one call to measure the interval and one to store the timestamp, per fetch
    mocker.patch(
        "tiddl.core.api.client.monotonic", side_effect=[10.0, 10.0, 10.1, 10.1]
    )

    mock_session = mocker.Mock()
    mock_session.get.return_value = build_response(mocker, 200, {"foo": "bar"})

    client = TidalClient("token", tmp_path / "cache", min_request_interval=0.25)
    client.session = mock_session

    client.fetch(DummyModel, "albums/123")
    client.fetch(DummyModel, "albums/456")

    # nothing to wait for on the first request, 0.15s left on the second
    mock_sleep.assert_called_once_with(pytest.approx(0.15))


def test_fetch_does_not_throttle_cached_responses(
    mocker: MockerFixture, tmp_path: Path
):
    mock_sleep = mocker.patch("tiddl.core.api.client.sleep")
    mocker.patch("tiddl.core.api.client.monotonic", side_effect=[10.0, 10.01])

    mock_session = mocker.Mock()
    mock_session.get.return_value = build_response(
        mocker, 200, {"foo": "bar"}, from_cache=True
    )

    client = TidalClient("token", tmp_path / "cache", min_request_interval=0.25)
    client.session = mock_session

    client.fetch(DummyModel, "albums/123")
    client.fetch(DummyModel, "albums/456")

    mock_sleep.assert_not_called()
