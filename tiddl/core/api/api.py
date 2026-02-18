from logging import getLogger
from typing import Literal, TypeAlias

from requests_cache import DO_NOT_CACHE, EXPIRE_IMMEDIATELY

log = getLogger(__name__)

from .client import TidalClient
from .models.base import (
    AlbumItems,
    AlbumItemsCredits,
    ArtistAlbumsItems,
    ArtistVideosItems,
    Favorites,
    MixItems,
    PlaylistItems,
    Search,
    SessionResponse,
    TrackLyrics,
    TrackStream,
    VideoStream,
)
from .models.resources import (
    Album,
    Artist,
    Playlist,
    StreamVideoQuality,
    Track,
    TrackQuality,
    Video,
)
from .models.review import AlbumReview

ID: TypeAlias = str | int


class Limits:
    # TODO test every max limit

    ARTIST_ALBUMS = 10
    ARTIST_ALBUMS_MAX = 100

    ARTIST_VIDEOS = 10
    ARTIST_VIDEOS_MAX = 100

    ALBUM_ITEMS = 20
    ALBUM_ITEMS_MAX = 100

    PLAYLIST_ITEMS = 20
    PLAYLIST_ITEMS_MAX = 100

    MIX_ITEMS = 20
    MIX_ITEMS_MAX = 100


class TidalAPI:
    client: TidalClient
    user_id: str
    country_code: str

    def __init__(self, client: TidalClient, user_id: str, country_code: str) -> None:
        self.client = client
        self.user_id = user_id
        self.country_code = country_code

    @staticmethod
    def _filter_unavailable_items(data: dict) -> dict:
        """Remove items whose track has no ISRC (unavailable/region-locked tracks).

        Short-circuits if nothing is filtered to avoid unnecessary allocation.
        """
        items = data["items"]
        available = []
        for i in items:
            track = i.get("item")
            if track and track.get("isrc") is not None:
                available.append(i)
            else:
                log.warning(
                    f"Skipping unavailable track: '{track['title']}' (ID: {track['id']})"
                    if track
                    else "Skipping item with missing track data"
                )
        if len(available) == len(items):
            return data
        return {**data, "items": available}

    def get_album(self, album_id: ID):
        return self.client.fetch(
            Album,
            f"albums/{album_id}",
            {"countryCode": self.country_code},
            expire_after=3600,
        )

    def get_album_items(
        self, album_id: ID, limit: int = Limits.ALBUM_ITEMS, offset: int = 0
    ):
        return self.client.fetch(
            AlbumItems,
            f"albums/{album_id}/items",
            {
                "countryCode": self.country_code,
                "limit": min(limit, Limits.ALBUM_ITEMS_MAX),
                "offset": offset,
            },
            expire_after=3600,
        )

    def get_album_items_credits(
        self, album_id: ID, limit: int = Limits.ALBUM_ITEMS, offset: int = 0
    ):
        return self.client.fetch(
            AlbumItemsCredits,
            f"albums/{album_id}/items/credits",
            {
                "countryCode": self.country_code,
                "limit": min(limit, Limits.ALBUM_ITEMS_MAX),
                "offset": offset,
            },
            expire_after=3600,
        )

    def get_album_review(self, album_id: ID):
        return self.client.fetch(
            AlbumReview,
            f"albums/{album_id}/review",
            {"countryCode": self.country_code},
            expire_after=3600,
        )

    def get_artist(self, artist_id: ID):
        return self.client.fetch(
            Artist,
            f"artists/{artist_id}",
            {"countryCode": self.country_code},
            expire_after=3600,
        )

    def get_artist_videos(
        self,
        artist_id: ID,
        limit: int = Limits.ARTIST_VIDEOS,
        offset: int = 0,
    ):
        return self.client.fetch(
            ArtistVideosItems,
            f"artists/{artist_id}/videos",
            {
                "countryCode": self.country_code,
                "limit": limit,
                "offset": offset,
            },
            expire_after=3600,
        )

    def get_artist_albums(
        self,
        artist_id: ID,
        limit: int = Limits.ARTIST_ALBUMS,
        offset: int = 0,
        filter: Literal["ALBUMS", "EPSANDSINGLES"] = "ALBUMS",
    ):
        return self.client.fetch(
            ArtistAlbumsItems,
            f"artists/{artist_id}/albums",
            {
                "countryCode": self.country_code,
                "limit": min(limit, Limits.ARTIST_ALBUMS_MAX),
                "offset": offset,
                "filter": filter,
            },
            expire_after=3600,
        )

    def get_mix_items(
        self,
        mix_id: str,
        limit: int = Limits.MIX_ITEMS,
        offset: int = 0,
        skip_unavailable_tracks: bool = False,
    ):
        return self.client.fetch(
            MixItems,
            f"mixes/{mix_id}/items",
            {
                "countryCode": self.country_code,
                "limit": min(limit, Limits.MIX_ITEMS_MAX),
                "offset": offset,
            },
            expire_after=3600,
            pre_validate=self._filter_unavailable_items if skip_unavailable_tracks else None,
        )

    def get_favorites(self):
        return self.client.fetch(
            Favorites,
            f"users/{self.user_id}/favorites/ids",
            {"countryCode": self.country_code},
            expire_after=EXPIRE_IMMEDIATELY,
        )

    def get_playlist(self, playlist_uuid: str):
        return self.client.fetch(
            Playlist,
            f"playlists/{playlist_uuid}",
            {"countryCode": self.country_code},
            expire_after=EXPIRE_IMMEDIATELY,
        )

    def get_playlist_items(
        self,
        playlist_uuid: str,
        limit: int = Limits.PLAYLIST_ITEMS,
        offset: int = 0,
        skip_unavailable_tracks: bool = False,
    ):
        return self.client.fetch(
            PlaylistItems,
            f"playlists/{playlist_uuid}/items",
            {
                "countryCode": self.country_code,
                "limit": min(limit, Limits.PLAYLIST_ITEMS_MAX),
                "offset": offset,
            },
            expire_after=EXPIRE_IMMEDIATELY,
            pre_validate=self._filter_unavailable_items if skip_unavailable_tracks else None,
        )

    def get_search(self, query: str):
        return self.client.fetch(
            Search,
            "search",
            {"countryCode": self.country_code, "query": query},
            expire_after=DO_NOT_CACHE,
        )

    def get_session(self):
        return self.client.fetch(SessionResponse, "sessions", expire_after=DO_NOT_CACHE)

    def get_track_lyrics(self, track_id: ID):
        return self.client.fetch(
            TrackLyrics,
            f"tracks/{track_id}/lyrics",
            {"countryCode": self.country_code},
            expire_after=3600,
        )

    def get_track(self, track_id: ID):
        return self.client.fetch(
            Track,
            f"tracks/{track_id}",
            {"countryCode": self.country_code},
            expire_after=3600,
        )

    def get_track_stream(self, track_id: ID, quality: TrackQuality):
        return self.client.fetch(
            TrackStream,
            f"tracks/{track_id}/playbackinfopostpaywall",
            {
                "audioquality": quality,
                "playbackmode": "STREAM",
                "assetpresentation": "FULL",
            },
            expire_after=DO_NOT_CACHE,
        )

    def get_video(self, video_id: ID):
        return self.client.fetch(
            Video,
            f"videos/{video_id}",
            {"countryCode": self.country_code},
            expire_after=3600,
        )

    def get_video_stream(self, video_id: ID, quality: StreamVideoQuality):
        return self.client.fetch(
            VideoStream,
            f"videos/{video_id}/playbackinfopostpaywall",
            {
                "videoquality": quality,
                "playbackmode": "STREAM",
                "assetpresentation": "FULL",
            },
            expire_after=DO_NOT_CACHE,
        )
