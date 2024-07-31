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


class TidalApi:
    def __init__(self, token: str, user_id: str, country_code: str) -> None:
        self.token = token
        self.user_id = user_id
        self.country_code = country_code

        self._session = Session()
        self._session.headers = {"authorization": f"Bearer {token}"}
        self._logger = logging.getLogger("TidalApi")

    def _request(self, endpoint: str, params={}):
        self._logger.debug(f"{endpoint} {params}")
        req = self._session.request(
            method="GET", url=f"{API_URL}/{endpoint}", params=params
        )

        # TODO: endpoints error handling ✨

        return req.json()

    def getSession(self) -> SessionResponse:
        return self._request(
            f"sessions",
        )

    def getTrackStream(self, id: str, quality: TrackQuality) -> TrackStream:
        return self._request(
            f"tracks/{id}/playbackinfo",
            {
                "audioquality": quality,
                "playbackmode": "STREAM",
                "assetpresentation": "FULL",
            },
        )

    def getTrack(self, id: str) -> Track:
        return self._request(f"tracks/{id}", {"countryCode": self.country_code})

    def getArtistAlbums(self, id: str, limit=10, offset=0) -> AristAlbumsItems:
        return self._request(
            f"artists/{id}/albums",
            {"countryCode": self.country_code, "limit": limit, "offset": offset},
        )

    def getAlbum(self, id: str) -> Album:
        return self._request(f"albums/{id}", {"countryCode": self.country_code})

    def getAlbumItems(self, id: str, limit=10, offset=0) -> AlbumItems:
        return self._request(
            f"albums/{id}/items",
            {"countryCode": self.country_code, "limit": limit, "offset": offset},
        )

    def getPlaylist(self, uuid: str) -> Playlist:
        return self._request(
            f"playlists/{uuid}",
            {"countryCode": self.country_code},
        )

    def getPlaylistItems(self, uuid: str, limit=10, offset=0) -> PlaylistItems:
        return self._request(
            f"playlists/{uuid}/items",
            {"countryCode": self.country_code, "limit": limit, "offset": offset},
        )
