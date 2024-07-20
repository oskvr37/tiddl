from requests import request
from .types import DeviceAuthData, AuthData

AUTH_URL = "https://auth.tidal.com/v1/oauth2"
CLIENT_ID = "7m7Ap0JC9j1cOM3n"
CLIENT_SECRET = "vRAdA108tlvkJpTsGZS8rGZ7xTlbJ0qaZ2K9saEzsgY="


def getDeviceAuth() -> DeviceAuthData:
    return request(
        "POST",
        f"{AUTH_URL}/device_authorization",
        data={"client_id": CLIENT_ID, "scope": "r_usr+w_usr+w_sub"},
    ).json()


def getToken(device_code: str) -> AuthData:
    return request(
        "POST",
        f"{AUTH_URL}/token",
        data={
            "client_id": CLIENT_ID,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "scope": "r_usr+w_usr+w_sub",
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
    ).json()
