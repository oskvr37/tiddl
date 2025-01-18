import logging
from requests import Session

from .exceptions import AuthError, ApiError
from .models import (
    SessionResponse,
    TrackQuality,
    Track,
    TrackStream,
    AristAlbumsItems,
    Album,
    AlbumItems,
    Playlist,
    PlaylistItems,
    Favorites,
    Search,
)

API_URL = "https://api.tidal.com/v1"

# Tidal default limits
ARTIST_ALBUMS_LIMIT = 50
ALBUM_ITEMS_LIMIT = 10
PLAYLIST_LIMIT = 50


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

        data = req.json()

        if req.status_code == 401:
            raise AuthError(**data)

        if req.status_code != 200:
            raise ApiError(**data)

        return data

    def getSession(self):
        return SessionResponse(
            **self._request(
                "sessions",
            )
        )

    def getTrackStream(self, id: str | int, quality: TrackQuality):
        return TrackStream(
            **self._request(
                f"tracks/{id}/playbackinfo",
                {
                    "audioquality": quality,
                    "playbackmode": "STREAM",
                    "assetpresentation": "FULL",
                },
            )
        )

    def getTrack(self, id: str | int):
        return Track(
            **self._request(f"tracks/{id}", {"countryCode": self.country_code})
        )

    def getArtistAlbums(
        self, id: str | int, limit=ARTIST_ALBUMS_LIMIT, offset=0, onlyNonAlbum=False
    ):
        params = {"countryCode": self.country_code, "limit": limit, "offset": offset}

        if onlyNonAlbum:
            params.update({"filter": "EPSANDSINGLES"})

        return AristAlbumsItems(
            **self._request(
                f"artists/{id}/albums",
                params,
            )
        )

    def getAlbum(self, id: str | int):
        return Album(
            **self._request(f"albums/{id}", {"countryCode": self.country_code})
        )

    def getAlbumItems(self, id: str | int, limit=ALBUM_ITEMS_LIMIT, offset=0):
        return AlbumItems(
            **self._request(
                f"albums/{id}/items",
                {"countryCode": self.country_code, "limit": limit, "offset": offset},
            )
        )

    def getPlaylist(self, uuid: str):
        return Playlist(
            **self._request(
                f"playlists/{uuid}",
                {"countryCode": self.country_code},
            )
        )

    def getPlaylistItems(self, uuid: str, limit=PLAYLIST_LIMIT, offset=0):
        return PlaylistItems(
            **self._request(
                f"playlists/{uuid}/items",
                {"countryCode": self.country_code, "limit": limit, "offset": offset},
            )
        )

    def getFavorites(self):
        return Favorites(
            **self._request(
                f"users/{self.user_id}/favorites/ids",
                {"countryCode": self.country_code},
            )
        )

    def search(self, query: str):
        return Search(
            **self._request(
                "search", {"countryCode": self.country_code, "query": query}
            )
        )
