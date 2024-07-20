from requests import request, Response
from typing import Literal

from .types import DeviceAuthData, AuthData

AUTH_URL = "https://auth.tidal.com/v1/oauth2"
CLIENT_ID = "7m7Ap0JC9j1cOM3n"
CLIENT_SECRET = "vRAdA108tlvkJpTsGZS8rGZ7xTlbJ0qaZ2K9saEzsgY="


class TidalApi:
    def request(
        self, method: Literal["GET", "POST"], url: str, data=None, auth=None
    ) -> Response:
        req = request(method, url, data=data, auth=auth)

        if req.status_code != 200:
            raise Exception(f"Bad response - {req.status_code}")

        return req

    def getDeviceAuth(self) -> DeviceAuthData:
        return self.request(
            "POST",
            f"{AUTH_URL}/device_authorization",
            {"client_id": CLIENT_ID, "scope": "r_usr+w_usr+w_sub"},
        ).json()

    def getToken(self, device_code: str) -> AuthData:
        return self.request(
            "POST",
            f"{AUTH_URL}/token",
            {
                "client_id": CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "scope": "r_usr+w_usr+w_sub",
            },
            (CLIENT_ID, CLIENT_SECRET),
        ).json()
