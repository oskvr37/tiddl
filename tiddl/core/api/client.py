import json
from logging import getLogger
from pathlib import Path
from random import random
from typing import Any, Type, TypeVar, Callable, Optional

from pydantic import BaseModel
from time import monotonic, sleep

from requests import Response
from requests.exceptions import JSONDecodeError
from requests_cache import (
    CachedSession,
    StrOrPath,
    NEVER_EXPIRE,
)

from .exceptions import ApiError, RateLimitError

T = TypeVar("T", bound=BaseModel)

API_URL = "https://api.tidal.com/v1"
MAX_RETRIES = 5
RETRY_DELAY = 2

TOO_MANY_REQUESTS = 429

# rate limits are transient, so they get their own, more patient retry budget
RATE_LIMIT_MAX_RETRIES = 8
RATE_LIMIT_MAX_BACKOFF = 60.0

# minimum seconds between two requests that actually reach the API
MIN_REQUEST_INTERVAL = 0.25

log = getLogger(__name__)


# TODO add token expiry check
# maybe refactor to aiohttp.ClientSession
class TidalClient:
    _token: str
    debug_path: Path | None
    session: CachedSession
    on_token_expiry: Optional[Callable[[], str | None]]
    min_request_interval: float
    rate_limit_max_retries: int
    rate_limit_max_backoff: float

    def __init__(
        self,
        token: str,
        cache_name: StrOrPath,
        omit_cache: bool = False,
        debug_path: Path | None = None,
        on_token_expiry: Optional[Callable[[], str | None]] = None,
        min_request_interval: float = MIN_REQUEST_INTERVAL,
        rate_limit_max_retries: int = RATE_LIMIT_MAX_RETRIES,
        rate_limit_max_backoff: float = RATE_LIMIT_MAX_BACKOFF,
    ) -> None:
        self.on_token_expiry = on_token_expiry
        self.debug_path = debug_path
        self.session = CachedSession(
            cache_name=cache_name, always_revalidate=omit_cache
        )
        self.session.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        self._token = token
        self.min_request_interval = min_request_interval
        self.rate_limit_max_retries = rate_limit_max_retries
        self.rate_limit_max_backoff = rate_limit_max_backoff
        self._last_api_request = 0.0

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token: str):
        self._token = token
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
            }
        )

    def _throttle(self) -> None:
        """
        Keep `min_request_interval` between requests that reach the API.

        Cached responses do not update the timestamp, so a run with a warm
        cache is not slowed down at all.
        """

        if self.min_request_interval <= 0:
            return

        elapsed = monotonic() - self._last_api_request

        if 0 <= elapsed < self.min_request_interval:
            sleep(self.min_request_interval - elapsed)

    def _rate_limit_delay(self, res: Response, attempt: int) -> float:
        """
        Seconds to wait after a `429`: `Retry-After` when the API sends it,
        otherwise exponential backoff with jitter.
        """

        retry_after = res.headers.get("Retry-After")

        if retry_after:
            try:
                delay = float(retry_after)
            except ValueError:
                # Retry-After may also be an HTTP date, fall back to backoff
                log.debug(f"unparsable Retry-After header: {retry_after!r}")
            else:
                if delay > self.rate_limit_max_backoff:
                    log.warning(
                        f"Retry-After of {delay}s exceeds the "
                        f"{self.rate_limit_max_backoff}s backoff limit"
                    )

                return min(delay, self.rate_limit_max_backoff)

        backoff = min(
            RETRY_DELAY * 2 ** (attempt - 1),
            self.rate_limit_max_backoff,
        )

        # jitter the second half of the delay to desynchronize retries
        return backoff / 2 + random() * backoff / 2

    def fetch(
        self,
        model: Type[T],
        endpoint: str,
        params: dict[str, Any] = {},
        expire_after: int = NEVER_EXPIRE,
        _attempt: int = 1,
        _rate_limit_attempt: int = 1,
    ) -> T:
        """
        Fetch data from the API endpoint
        and parse it into the given Pydantic model.
        """

        self._throttle()

        res = self.session.get(
            f"{API_URL}/{endpoint}", params=params, expire_after=expire_after
        )

        if not res.from_cache:
            self._last_api_request = monotonic()

        if res.status_code == 401 and self.on_token_expiry:
            token = self.on_token_expiry()

            if token:
                self.token = token

            return self.fetch(
                model=model,
                endpoint=endpoint,
                params=params,
                expire_after=expire_after,
                _attempt=MAX_RETRIES - 1,
                _rate_limit_attempt=_rate_limit_attempt,
            )

        log.debug(
            f"{endpoint} {params} '{'HIT' if res.from_cache else 'MISS'}' [{res.status_code}]",
        )

        # a rate limited response usually has no json body at all,
        # so it has to be handled before parsing
        if res.status_code == TOO_MANY_REQUESTS:
            if _rate_limit_attempt >= self.rate_limit_max_retries:
                log.error(
                    f"rate limited on '{endpoint}', "
                    f"gave up after {self.rate_limit_max_retries} attempts"
                )
                raise RateLimitError(
                    userMessage="Rate limited by Tidal API, try again later."
                )

            delay = self._rate_limit_delay(res, _rate_limit_attempt)

            log.warning(
                f"rate limited on '{endpoint}', waiting {delay:.1f}s, "
                f"retrying {_rate_limit_attempt}/{self.rate_limit_max_retries}"
            )
            sleep(delay)

            return self.fetch(
                model=model,
                endpoint=endpoint,
                params=params,
                expire_after=expire_after,
                _attempt=_attempt,
                _rate_limit_attempt=_rate_limit_attempt + 1,
            )

        try:
            data = res.json()
        except JSONDecodeError as e:
            if _attempt >= MAX_RETRIES:
                log.error(f"JSON decode failed after {MAX_RETRIES} attempts: {e}")
                raise ApiError(
                    status=res.status_code,
                    subStatus="0",
                    userMessage="Response body does not contain valid json.",
                )

            log.warning(f"JSON decode error, retrying {_attempt}/{MAX_RETRIES}")
            sleep(RETRY_DELAY)

            return self.fetch(
                model=model,
                endpoint=endpoint,
                params=params,
                expire_after=expire_after,
                _attempt=_attempt + 1,
                _rate_limit_attempt=_rate_limit_attempt,
            )

        if self.debug_path:
            file = self.debug_path / f"{endpoint}.json"
            file.parent.mkdir(parents=True, exist_ok=True)

            file.write_text(
                json.dumps(
                    {
                        "status_code": res.status_code,
                        "endpoint": endpoint,
                        "params": params,
                        "data": data,
                    },
                    indent=2,
                )
            )

        if res.status_code != 200:
            log.error(f"{endpoint=}, {params=}, {data=}")
            raise ApiError(**data)

        return model.model_validate(data)
