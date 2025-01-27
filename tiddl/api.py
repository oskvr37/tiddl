import json
import logging
from pathlib import Path
from typing import Any, Literal, Type, TypeVar

from pydantic import BaseModel
from requests import Session

from tiddl.models.api import (
    Album,
    AlbumItems,
    Artist,
    ArtistAlbumsItems,
    Favorites,
    Playlist,
    PlaylistItems,
    Search,
    SessionResponse,
    Track,
    TrackStream,
    Video,
)

from tiddl.models.constants import TrackQuality
from tiddl.exceptions import ApiError

DEBUG = False
T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


def ensureLimit(limit: int, max_limit: int) -> int:
    if limit > max_limit:
        logger.warning(f"Max limit is {max_limit}")
        return max_limit

    return limit


class Limits:
    ARTIST_ALBUMS = 50
    ALBUM_ITEMS = 10
    ALBUM_ITEMS_MAX = 100
    PLAYLIST = 50


class TidalApi:
    URL = "https://api.tidal.com/v1"
    LIMITS = Limits

    def __init__(self, token: str, user_id: str, country_code: str) -> None:
        self.user_id = user_id
        self.country_code = country_code

        self.session = Session()
        self.session.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def fetch(
        self, model: Type[T], endpoint: str, params: dict[str, Any] = {}
    ) -> T:
        """Fetch data from the API and parse it into the given Pydantic model."""

        req = self.session.get(f"{self.URL}/{endpoint}", params=params)

        logger.debug((endpoint, params, req.status_code))

        data = req.json()

        if DEBUG:
            debug_data = {
                "status_code": req.status_code,
                "endpoint": endpoint,
                "params": params,
                "data": data,
            }

            path = Path(f"debug_data/{endpoint}.json")
            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open("w", encoding="utf-8") as f:
                json.dump(debug_data, f, indent=2)

        if req.status_code != 200:
            raise ApiError(**data)

        return model.model_validate(data)

    def getAlbum(self, album_id: str | int):
        return self.fetch(
            Album, f"albums/{album_id}", {"countryCode": self.country_code}
        )

    def getAlbumItems(
        self, album_id: str | int, limit=LIMITS.ALBUM_ITEMS, offset=0
    ):
        return self.fetch(
            AlbumItems,
            f"albums/{album_id}/items",
            {
                "countryCode": self.country_code,
                "limit": ensureLimit(limit, self.LIMITS.ALBUM_ITEMS_MAX),
                "offset": offset,
            },
        )

    def getArtist(self, artist_id: str | int):
        return self.fetch(
            Artist, f"artists/{artist_id}", {"countryCode": self.country_code}
        )

    def getArtistAlbums(
        self,
        artist_id: str | int,
        limit=LIMITS.ARTIST_ALBUMS,
        offset=0,
        filter: Literal["ALBUMS", "EPSANDSINGLES"] = "ALBUMS",
    ):
        return self.fetch(
            ArtistAlbumsItems,
            f"artists/{artist_id}/albums",
            {
                "countryCode": self.country_code,
                "limit": limit,  # tested limit 10,000
                "offset": offset,
                "filter": filter,
            },
        )

    def getFavorites(self):
        return self.fetch(
            Favorites,
            f"users/{self.user_id}/favorites/ids",
            {"countryCode": self.country_code},
        )

    def getPlaylist(self, playlist_uuid: str):
        return self.fetch(
            Playlist,
            f"playlists/{playlist_uuid}",
            {"countryCode": self.country_code},
        )

    def getPlaylistItems(
        self, playlist_uuid: str, limit=LIMITS.PLAYLIST, offset=0
    ):
        return self.fetch(
            PlaylistItems,
            f"playlists/{playlist_uuid}/items",
            {
                "countryCode": self.country_code,
                "limit": limit,
                "offset": offset,
            },
        )

    def getSearch(self, query: str):
        return self.fetch(
            Search, "search", {"countryCode": self.country_code, "query": query}
        )

    def getSession(self):
        return self.fetch(SessionResponse, "sessions")

    def getTrack(self, track_id: str | int):
        return self.fetch(
            Track, f"tracks/{track_id}", {"countryCode": self.country_code}
        )

    def getTrackStream(self, track_id: str | int, quality: TrackQuality):
        return self.fetch(
            TrackStream,
            f"tracks/{track_id}/playbackinfo",
            {
                "audioquality": quality,
                "playbackmode": "STREAM",
                "assetpresentation": "FULL",
            },
        )

    def getVideo(self, video_id: str | int):
        return self.fetch(
            Video, f"videos/{video_id}", {"countryCode": self.country_code}
        )
