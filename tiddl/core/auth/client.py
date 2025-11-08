import base64
from os import environ
from requests import request
from typing import Any, TypeAlias

from tiddl.core.auth.exceptions import AuthClientError


def get_auth_credentials() -> tuple[str, str]:
    ENV_KEY = "TIDDL_AUTH"

    client_id, client_secret = (
        base64.b64decode(
            "ZlgySnhkbW50WldLMGl4VDsxTm45QWZEQWp4cmdKRkpiS05XTGVBeUtHVkdtSU51WFBQTEhWWEF2eEFnPQ=="
        )
        .decode()
        .split(";")
    )

    env_value = environ.get(ENV_KEY, None)

    if env_value:
        client_id, client_secret = env_value.split(";")

    return client_id, client_secret


AUTH_URL = "https://auth.tidal.com/v1/oauth2"
CLIENT_ID, CLIENT_SECRET = get_auth_credentials()

JSON: TypeAlias = dict[str, Any]


class AuthClient:

    def __init__(self) -> None:
        self.auth_url = AUTH_URL
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET

    def get_device_auth(self) -> JSON:
        res = request(
            "POST",
            f"{self.auth_url}/device_authorization",
            data={"client_id": self.client_id, "scope": "r_usr+w_usr+w_sub"},
        )

        res.raise_for_status()

        return res.json()

    def get_auth(self, device_code: str) -> JSON:
        res = request(
            "POST",
            f"{self.auth_url}/token",
            data={
                "client_id": self.client_id,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "scope": "r_usr+w_usr+w_sub",
            },
            auth=(self.client_id, self.client_secret),
        )

        json_data = res.json()

        if res.status_code != 200:
            raise AuthClientError(**json_data)

        return json_data

    def refresh_token(self, refresh_token: str) -> JSON:
        res = request(
            "POST",
            f"{self.auth_url}/token",
            data={
                "client_id": self.client_id,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": "r_usr+w_usr+w_sub",
            },
            auth=(self.client_id, self.client_secret),
        )

        res.raise_for_status()

        return res.json()

    def logout_token(self, access_token: str) -> None:
        res = request(
            "POST",
            "https://api.tidal.com/v1/logout",
            headers={"authorization": f"Bearer {access_token}"},
        )

        res.raise_for_status()
