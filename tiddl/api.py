from requests import Session
from .types import SessionData, PlaylistResponse, TrackResponse

API_URL = "https://api.tidal.com/v1"


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
            f"{API_URL}/sessions",
        ).json()

    def getPlaylists(self) -> PlaylistResponse:
        return self.session.get(
            f"{API_URL}/users/{self.user_id}/playlists",
            params={"countryCode": self.country_code},
        ).json()

    def getTrack(self, id: int, quality="LOW") -> TrackResponse:
        # TODO: add quality types 🏷️

        return self.session.get(
            f"{API_URL}/tracks/{id}/playbackinfo",
            params={
                "audioquality": quality,
                "playbackmode": "STREAM",
                "assetpresentation": "FULL",
            },
        ).json()
