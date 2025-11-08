import typer

from rich.console import Console
from pathlib import Path

from tiddl.core.api import TidalClient, TidalAPI
from tiddl.cli.config import APP_PATH
from tiddl.cli.utils.auth.core import load_auth_data
from tiddl.cli.utils.resource import TidalResource


class ContextObject:
    console: Console
    resources: list[TidalResource]
    _api: TidalAPI | None
    api_omit_cache: bool
    debug_path: Path | None

    def __init__(
        self, api_omit_cache: bool, debug_path: Path | None, console: Console
    ) -> None:
        self.console = console
        self.resources = []
        self._api = None
        self.api_omit_cache = api_omit_cache
        self.debug_path = debug_path

    @property
    def api(self):
        if self._api is not None:
            return self._api

        auth_data = load_auth_data()

        assert auth_data.token, "Auth Token is missing. Use `tiddl auth login`"
        assert auth_data.user_id, "User ID is missing. Use `tiddl auth login`"
        assert auth_data.country_code, "Country Code is missing. Use `tiddl auth login`"

        client = TidalClient(
            token=auth_data.token,
            cache_name=APP_PATH / "api_cache",
            omit_cache=self.api_omit_cache,
            debug_path=self.debug_path,
        )

        self._api = TidalAPI(client, auth_data.user_id, auth_data.country_code)

        return self._api


class Context(typer.Context):
    obj: ContextObject
