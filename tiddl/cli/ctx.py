import typer
from time import time
from pathlib import Path

from rich.console import Console

from tiddl.core.api import TidalClient, TidalAPI
from tiddl.cli.config import APP_PATH
from tiddl.core.auth import AuthAPI, PlaybackProfile, ProfileTokenManager
from tiddl.cli.utils.auth.core import load_auth_data, save_auth_data
from tiddl.cli.utils.resource import TidalResource


class ContextObject:
    console: Console
    resources: list[TidalResource]
    auth_api: AuthAPI
    _api: TidalAPI | None
    _profile_apis: dict[PlaybackProfile, TidalAPI]
    _profile_token_manager: ProfileTokenManager | None
    _playback_user_id: str | None
    _playback_country_code: str | None
    api_omit_cache: bool
    debug_path: Path | None

    def __init__(
        self, api_omit_cache: bool, debug_path: Path | None, console: Console
    ) -> None:
        self.console = console
        self.resources = []
        self.auth_api = AuthAPI()
        self._api = None
        self._profile_apis = {}
        self._profile_token_manager = None
        self._playback_user_id = None
        self._playback_country_code = None
        self.api_omit_cache = api_omit_cache
        self.debug_path = debug_path

    def _persist_refresh_token(self, refresh_token: str) -> None:
        auth_data = load_auth_data()
        auth_data.refresh_token = refresh_token
        save_auth_data(auth_data=auth_data)

    @property
    def api(self):
        if self._api is not None:
            return self._api

        auth_data = load_auth_data()

        assert auth_data.token, "Auth Token is missing. Use `tiddl auth login`"
        assert auth_data.user_id, "User ID is missing. Use `tiddl auth login`"
        assert auth_data.country_code, "Country Code is missing. Use `tiddl auth login`"

        assert auth_data.refresh_token, (
            "Refresh Token is missing. Use `tiddl auth login`"
        )

        def on_token_expiry() -> str:
            latest_auth_data = load_auth_data()
            assert latest_auth_data.refresh_token
            auth_response = self.auth_api.refresh_token(latest_auth_data.refresh_token)
            latest_auth_data.token = auth_response.access_token
            latest_auth_data.expires_at = auth_response.expires_in + int(time())

            if auth_response.refresh_token:
                latest_auth_data.refresh_token = auth_response.refresh_token
                if self._profile_token_manager:
                    self._profile_token_manager.replace_refresh_token(
                        auth_response.refresh_token
                    )

            save_auth_data(auth_data=latest_auth_data)

            return auth_response.access_token

        client = TidalClient(
            token=auth_data.token,
            cache_name=APP_PATH / "api_cache",
            omit_cache=self.api_omit_cache,
            debug_path=self.debug_path,
            on_token_expiry=on_token_expiry,
        )

        self._api = TidalAPI(client, auth_data.user_id, auth_data.country_code)

        return self._api

    def get_playback_api(self, profile: PlaybackProfile) -> TidalAPI:
        token_manager = self._profile_token_manager
        if token_manager is None:
            auth_data = load_auth_data()
            refresh_token = auth_data.refresh_token
            assert refresh_token, "Refresh Token is missing. Use `tiddl auth login`"
            assert auth_data.user_id, "User ID is missing. Use `tiddl auth login`"
            assert auth_data.country_code, (
                "Country Code is missing. Use `tiddl auth login`"
            )

            token_manager = ProfileTokenManager(
                refresh_token=refresh_token,
                on_refresh_token=self._persist_refresh_token,
            )
            self._profile_token_manager = token_manager
            self._playback_user_id = auth_data.user_id
            self._playback_country_code = auth_data.country_code

        profile_token = token_manager.get_token(profile)
        profile_api = self._profile_apis.get(profile)

        if profile_api is not None:
            if profile_api.client.token != profile_token.access_token:
                profile_api.client.token = profile_token.access_token
            return profile_api

        assert self._playback_user_id
        assert self._playback_country_code

        def on_token_expiry() -> str:
            assert self._profile_token_manager
            return self._profile_token_manager.get_token(
                profile, force=True
            ).access_token

        client = TidalClient(
            token=profile_token.access_token,
            client_id=profile_token.client_id,
            cache_name=APP_PATH / f"api_cache_{profile}",
            omit_cache=self.api_omit_cache,
            debug_path=self.debug_path,
            on_token_expiry=on_token_expiry,
        )
        profile_api = TidalAPI(
            client,
            self._playback_user_id,
            self._playback_country_code,
        )
        self._profile_apis[profile] = profile_api
        return profile_api


class Context(typer.Context):
    obj: ContextObject
