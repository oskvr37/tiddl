import json
from logging import getLogger
from pathlib import Path
from typing import Any, Type, TypeVar

from pydantic import BaseModel
from requests_cache import (
    CachedSession,
    StrOrPath,
    NEVER_EXPIRE,
)

from .exceptions import ApiError

T = TypeVar("T", bound=BaseModel)

API_URL = "https://api.tidal.com/v1"

log = getLogger(__name__)


class TidalClient:
    token: str
    debug_path: Path | None
    session: CachedSession

    def __init__(
        self,
        token: str,
        cache_name: StrOrPath,
        omit_cache: bool = False,
        debug_path: Path | None = None,
    ) -> None:
        self.token = token
        self.debug_path = debug_path

        self.session = CachedSession(
            cache_name=cache_name, always_revalidate=omit_cache
        )
        self.session.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def fetch(
        self,
        model: Type[T],
        endpoint: str,
        params: dict[str, Any] = {},
        expire_after: int = NEVER_EXPIRE,
    ) -> T:
        """
        Fetch data from the API endpoint
        and parse it into the given Pydantic model.
        """

        res = self.session.get(
            f"{API_URL}/{endpoint}", params=params, expire_after=expire_after
        )

        log.debug(
            f"{endpoint} {params} '{'HIT' if res.from_cache else 'MISS'}' [{res.status_code}]",
        )

        data = res.json()

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
            raise ApiError(**data)

        return model.model_validate(data)
