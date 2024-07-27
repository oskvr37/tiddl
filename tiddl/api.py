from requests import Session
from .types import SessionResponse, PlaylistResponse, TrackResponse, TrackQuality

API_URL = "https://api.tidal.com/v1"

# TODO: endpoints error handling ✨


class TidalApi:
    def __init__(self, token: str, user_id: str, country_code: str) -> None:
        self.token = token
        self.user_id = user_id
        self.country_code = country_code

        self.session = Session()
        self.session.headers = {"authorization": f"Bearer {token}"}

    def getSession(self) -> SessionResponse:
        return self.session.get(
            f"{API_URL}/sessions",
        ).json()

    def getPlaylists(self) -> PlaylistResponse:
        return self.session.get(
            f"{API_URL}/users/{self.user_id}/playlists",
            params={"countryCode": self.country_code},
        ).json()

    def getTrack(self, id: int, quality: TrackQuality) -> TrackResponse:
        return self.session.get(
            f"{API_URL}/tracks/{id}/playbackinfo",
            params={
                "audioquality": quality,
                "playbackmode": "STREAM",
                "assetpresentation": "FULL",
            },
        ).json()
