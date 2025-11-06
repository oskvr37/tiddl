from tiddl.core.auth.client import AuthClient
from tiddl.core.auth.models import (
    AuthDeviceResponse,
    AuthResponse,
    AuthResponseWithRefresh,
)


class AuthAPI:
    def __init__(self, client: AuthClient | None = None) -> None:
        self._client = client or AuthClient()

    def get_device_auth(self) -> AuthDeviceResponse:
        json_data = self._client.get_device_auth()
        return AuthDeviceResponse.model_validate(json_data)

    def get_auth(self, device_code: str) -> AuthResponseWithRefresh:
        json_data = self._client.get_auth(device_code)
        return AuthResponseWithRefresh.model_validate(json_data)

    def refresh_token(self, refresh_token: str) -> AuthResponse:
        json_data = self._client.refresh_token(refresh_token)
        return AuthResponse.model_validate(json_data)

    def logout_token(self, access_token: str) -> None:
        self._client.logout_token(access_token)
