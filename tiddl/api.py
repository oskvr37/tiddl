from requests import Session
from .types import SessionData, PlaylistResponse


class TidalApi:
    def __init__(self, token: str) -> None:
        self.token = token

        self.session = Session()
        self.session.headers = {"authorization": f"Bearer {token}"}

        session_data = self.getSession()
        self.user_id = session_data["userId"]
        self.country_code = session_data["countryCode"]

    def getSession(self) -> SessionData:
        return self.session.get(
            "https://api.tidal.com/v1/sessions",
        ).json()

    def getPlaylists(self) -> PlaylistResponse:
        return self.session.get(
            f"https://api.tidalhifi.com/v1/users/{self.user_id}/playlists?countryCode={self.country_code}",
        ).json()
