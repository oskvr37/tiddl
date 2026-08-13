from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock
from time import time
from typing import Literal

from tiddl.core.auth.client import (
    CLIENT_ID,
    CLIENT_SECRET,
    AuthClient,
)
from tiddl.core.auth.models import AuthTokenResponse

PlaybackProfile = Literal["hires", "atmos"]


@dataclass(frozen=True)
class ClientProfile:
    client_id: str
    client_secret: str
    refresh_with_basic_auth: bool


@dataclass(frozen=True)
class ProfileToken:
    access_token: str
    client_id: str
    expires_at: float


# TIDAL exposes different playback capabilities to different client profiles.
# Both access tokens can be derived from the refresh token created by one login.
PLAYBACK_SCOPE = "r_usr+w_usr"
CLIENT_PROFILES: dict[PlaybackProfile, ClientProfile] = {
    "hires": ClientProfile(
        client_id="6BDSRdpK9hqEBTgU",
        client_secret="xeuPmY7nbpZ9IIbLAcQ93shka1VNheUAqN6IcszjTG8=",
        refresh_with_basic_auth=False,
    ),
    "atmos": ClientProfile(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        refresh_with_basic_auth=True,
    ),
}


def select_playback_profile(
    atmos_filter: Literal["none", "only", "allow"],
    atmos_available: bool,
) -> PlaybackProfile:
    if atmos_filter == "none":
        return "hires"

    if atmos_filter == "only" or atmos_available:
        return "atmos"

    return "hires"


class ProfileTokenManager:
    """Derive and cache capability-specific access tokens from one login."""

    def __init__(
        self,
        refresh_token: str,
        on_refresh_token: Callable[[str], None] | None = None,
        clock: Callable[[], float] = time,
        expiry_margin: int = 60,
        client_factory: Callable[[ClientProfile], AuthClient] | None = None,
    ) -> None:
        self._refresh_token = refresh_token
        self._on_refresh_token = on_refresh_token
        self._clock = clock
        self._expiry_margin = expiry_margin
        self._client_factory = client_factory or self._create_client
        self._tokens: dict[PlaybackProfile, ProfileToken] = {}
        self._lock = Lock()

    @staticmethod
    def _create_client(profile: ClientProfile) -> AuthClient:
        return AuthClient(
            client_id=profile.client_id,
            client_secret=profile.client_secret,
            refresh_with_basic_auth=profile.refresh_with_basic_auth,
            refresh_scope=PLAYBACK_SCOPE,
        )

    def get_token(
        self, profile_name: PlaybackProfile, force: bool = False
    ) -> ProfileToken:
        with self._lock:
            cached_token = self._tokens.get(profile_name)
            if (
                not force
                and cached_token
                and cached_token.expires_at > self._clock() + self._expiry_margin
            ):
                return cached_token

            profile = CLIENT_PROFILES[profile_name]
            client = self._client_factory(profile)
            response = AuthTokenResponse.model_validate(
                client.refresh_token(self._refresh_token)
            )

            if response.refresh_token and response.refresh_token != self._refresh_token:
                self._refresh_token = response.refresh_token
                if self._on_refresh_token:
                    self._on_refresh_token(response.refresh_token)

            token = ProfileToken(
                access_token=response.access_token,
                client_id=profile.client_id,
                expires_at=self._clock() + response.expires_in,
            )
            self._tokens[profile_name] = token
            return token

    def replace_refresh_token(self, refresh_token: str) -> None:
        """Keep the broker synchronized if another API refresh rotates the token."""
        with self._lock:
            self._refresh_token = refresh_token
