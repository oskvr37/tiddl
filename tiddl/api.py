import json
import logging
from pathlib import Path
from typing import Any, Literal, Type, TypeVar

from pydantic import BaseModel
from requests_cache import (
    CachedSession,
    EXPIRE_IMMEDIATELY,
    NEVER_EXPIRE,
    DO_NOT_CACHE,
)

from tiddl.models.api import (
    Album,
    AlbumItems,
    AlbumItemsCredits,
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
    VideoStream,
)

from tiddl.models.constants import TrackQuality
from tiddl.exceptions import ApiError
from tiddl.config import HOME_PATH

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

    def __init__(
        self, token: str, user_id: str, country_code: str, omit_cache=False
    ) -> None:
        self.user_id = user_id
        self.country_code = country_code

        # 3.0 TODO: change cache path
        CACHE_NAME = "tiddl_api_cache"

        self.session = CachedSession(
            cache_name=HOME_PATH / CACHE_NAME, always_revalidate=omit_cache
        )
        self.session.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def update_token(self, new_token: str):
        """Use to update the token in the session when using in server mode"""
        self.session.headers["Authorization"] = f"Bearer {new_token}"

    def fetch(
        self,
        model: Type[T],
        endpoint: str,
        params: dict[str, Any] = {},
        expire_after=NEVER_EXPIRE,
    ) -> T:
        """Fetch data from the API and parse it into the given Pydantic model."""

        req = self.session.get(
            f"{self.URL}/{endpoint}", params=params, expire_after=expire_after
        )

        logger.debug(
            (
                endpoint,
                params,
                req.status_code,
                "HIT" if req.from_cache else "MISS",
            )
        )

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

    def getAlbumItemsCredits(
        self, album_id: str | int, limit=LIMITS.ALBUM_ITEMS, offset=0
    ):
        return self.fetch(
            AlbumItemsCredits,
            f"albums/{album_id}/items/credits",
            {
                "countryCode": self.country_code,
                "limit": ensureLimit(limit, self.LIMITS.ALBUM_ITEMS_MAX),
                "offset": offset,
            },
        )

    def getArtist(self, artist_id: str | int):
        return self.fetch(
            Artist,
            f"artists/{artist_id}",
            {"countryCode": self.country_code},
            expire_after=3600,
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
            expire_after=3600,
        )

    def getFavorites(self):
        return self.fetch(
            Favorites,
            f"users/{self.user_id}/favorites/ids",
            {"countryCode": self.country_code},
            expire_after=EXPIRE_IMMEDIATELY,
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
            expire_after=EXPIRE_IMMEDIATELY,
        )

    def getSearch(self, query: str):
        return self.fetch(
            Search,
            "search",
            {"countryCode": self.country_code, "query": query},
            expire_after=EXPIRE_IMMEDIATELY,
        )

    def getSession(self):
        return self.fetch(
            SessionResponse, "sessions", expire_after=DO_NOT_CACHE
        )

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
            expire_after=DO_NOT_CACHE,
        )

    def getVideo(self, video_id: str | int):
        return self.fetch(
            Video, f"videos/{video_id}", {"countryCode": self.country_code}
        )

    def getVideoStream(self, video_id: str | int):
        return self.fetch(
            VideoStream,
            f"videos/{video_id}/playbackinfo",
            {
                "videoquality": "HIGH",
                "playbackmode": "STREAM",
                "assetpresentation": "FULL",
            },
            expire_after=DO_NOT_CACHE,
        )
