import logging
import base64
from os import environ

from requests import request

from tiddl.exceptions import AuthError
from tiddl.models import auth

AUTH_URL = "https://auth.tidal.com/v1/oauth2"


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


CLIENT_ID, CLIENT_SECRET = get_auth_credentials()

logger = logging.getLogger(__name__)


def getDeviceAuth():
    req = request(
        "POST",
        f"{AUTH_URL}/device_authorization",
        data={"client_id": CLIENT_ID, "scope": "r_usr+w_usr+w_sub"},
    )

    data = req.json()

    if req.status_code == 200:
        return auth.AuthDeviceResponse(**data)

    raise AuthError(**data)


def getToken(device_code: str):
    req = request(
        "POST",
        f"{AUTH_URL}/token",
        data={
            "client_id": CLIENT_ID,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "scope": "r_usr+w_usr+w_sub",
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
    )

    data = req.json()

    if req.status_code == 200:
        return auth.AuthResponseWithRefresh(**data)

    raise AuthError(**data)


def refreshToken(refresh_token: str):
    req = request(
        "POST",
        f"{AUTH_URL}/token",
        data={
            "client_id": CLIENT_ID,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": "r_usr+w_usr+w_sub",
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
    )

    data = req.json()

    if req.status_code == 200:
        return auth.AuthResponse(**data)

    raise AuthError(**data)


def removeToken(access_token: str):
    req = request(
        "POST",
        "https://api.tidal.com/v1/logout",
        headers={"authorization": f"Bearer {access_token}"},
    )

    logger.debug((req.status_code, req.text))
