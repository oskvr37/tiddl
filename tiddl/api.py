from requests import request, Response
from typing import Literal

from .types import SessionData


class TidalApi:
    def request(
        self,
        method: Literal["GET", "POST"],
        url: str,
        data=None,
        auth=None,
        headers=None,
    ) -> Response:
        req = request(method, url, data=data, auth=auth, headers=headers)

        if req.status_code != 200:
            raise Exception(f"{req.text} - {req.status_code}")

        return req

    def getSession(self, token: str) -> SessionData:
        return self.request(
            "GET",
            "https://api.tidal.com/v1/sessions",
            headers={"authorization": f"Bearer {token}"},
        ).json()

    def getPlaylists(self, token: str, user_id: int, country_code: str):
        return self.request(
            "GET",
            f"https://api.tidalhifi.com/v1/users/{user_id}/playlists?countryCode={country_code}",
            headers={"authorization": f"Bearer {token}"},
        ).json()
