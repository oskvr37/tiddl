import logging
from requests import Session

from .types import (
    SessionResponse,
    TrackQuality,
    Track,
    TrackStream,
    AristAlbumsItems,
    Album,
    AlbumItems,
    Playlist,
    PlaylistItems,
)

API_URL = "https://api.tidal.com/v1"

# TODO: endpoints error handling ✨


class TidalApi:
    def __init__(self, token: str, user_id: str, country_code: str) -> None:
        self.token = token
        self.user_id = user_id
        self.country_code = country_code

        self._session = Session()
        self._session.headers = {"authorization": f"Bearer {token}"}
        self._logger = logging.getLogger("TidalApi")

    def getSession(self) -> SessionResponse:
        return self._session.get(
            f"{API_URL}/sessions",
        ).json()

    def getTrackStream(self, id: int, quality: TrackQuality) -> TrackStream:
        self._logger.debug((id, quality))
        return self._session.get(
            f"{API_URL}/tracks/{id}/playbackinfo",
            params={
                "audioquality": quality,
                "playbackmode": "STREAM",
                "assetpresentation": "FULL",
            },
        ).json()

    def getTrack(self, id: int) -> Track:
        self._logger.debug(id)
        return self._session.get(
            f"{API_URL}/tracks/{id}", params={"countryCode": self.country_code}
        ).json()

    def getArtistAlbums(self, id: int) -> AristAlbumsItems:
        self._logger.debug(id)
        return self._session.get(
            f"{API_URL}/artists/{id}/albums", params={"countryCode": self.country_code}
        ).json()

    def getAlbum(self, id: int) -> Album:
        self._logger.debug(id)
        return self._session.get(
            f"{API_URL}/albums/{id}", params={"countryCode": self.country_code}
        ).json()

    def getAlbumItems(self, id: int) -> AlbumItems:
        self._logger.debug(id)
        return self._session.get(
            f"{API_URL}/albums/{id}/items", params={"countryCode": self.country_code}
        ).json()

    def getPlaylist(self, uuid: str) -> Playlist:
        return self._session.get(
            f"{API_URL}/playlists/{uuid}",
            params={"countryCode": self.country_code},
        ).json()

    def getPlaylistItems(self, uuid: str) -> PlaylistItems:
        return self._session.get(
            f"{API_URL}/playlists/{uuid}/items",
            params={"countryCode": self.country_code},
        ).json()
