from typing import Literal, TypeAlias

from requests_cache import DO_NOT_CACHE, EXPIRE_IMMEDIATELY
from pathlib import Path

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
    
    def get_album_lyrics(
        self, 
        album_id: str | int, 
        song_dir: Path, 
        skip_existing: bool = True
    ) -> bool:
        """
        Download lyrics for all tracks in an album as .lrc files
        Returns True if any lyrics were downloaded
        """
        import re
        from logging import getLogger
        
        log = getLogger(__name__)
        log.info("="*50)
        log.info(f"STARTING LYRICS DOWNLOAD - Album ID: {album_id}")
        log.info(f"Target directory: {song_dir}")
        log.info(f"Skip existing: {skip_existing}")
        log.info("="*50)
        
        lyrics_downloaded = False
        offset = 0
        
        while True:
            album_items = self.get_album_items(album_id=album_id, offset=offset)
            log.info(f"Got {len(album_items.items)} items at offset {offset}")
            
            for item in album_items.items:
                # Get the track from the item
                track = item.item if hasattr(item, 'item') else item
                
                # Skip if not a track
                if not hasattr(track, 'trackNumber'):
                    log.info(f"Skipping item {track.id} - not a track")
                    continue
                
                log.info(f"Processing: {track.trackNumber:02d} - {track.title}")
                
                # Build filename
                safe_title = re.sub(r'[<>:"/\\|?*]', '_', track.title)
                filename = f"{track.trackNumber:02d} - {safe_title}.lrc"
                lrc_path = song_dir / filename
                
                log.info(f"Lyrics file path: {lrc_path}")
                
                # Skip if exists
                if skip_existing and lrc_path.exists():
                    log.info(f"File already exists, skipping")
                    continue
                
                try:
                    log.info(f"Fetching lyrics for track {track.id}...")
                    lyrics = self.get_track_lyrics(track.id)
                    
                    if not lyrics.subtitles and not lyrics.lyrics:
                        log.info("No lyrics available for this track")
                        continue
                    
                    # Use subtitles if available, otherwise plain lyrics
                    content = lyrics.subtitles if lyrics.subtitles else lyrics.lyrics
                    
                    if not content:
                        log.info("Lyrics content is empty")
                        continue
                    
                    # Convert plain lyrics to basic LRC format
                    if not lyrics.subtitles and lyrics.lyrics:
                        log.info("Converting plain lyrics to LRC format")
                        lines = []
                        for line in lyrics.lyrics.splitlines():
                            if line.strip():
                                lines.append(f"[00:00.00]{line}")
                        content = "\n".join(lines)
                    
                    # Save file
                    lrc_path.parent.mkdir(parents=True, exist_ok=True)
                    with lrc_path.open('w', encoding='utf-8') as f:
                        f.write(content)
                    
                    log.info(f"✓ Successfully saved lyrics to {lrc_path}")
                    lyrics_downloaded = True
                    
                except Exception as e:
                    log.error(f"Error downloading lyrics for {track.title}: {e}")
                    import traceback
                    log.error(traceback.format_exc())
                    continue
            
            # Check if we got all items
            offset += album_items.limit
            if offset >= album_items.totalNumberOfItems:
                break
        
        log.info("="*50)
        log.info(f"LYRICS DOWNLOAD COMPLETE - Downloaded any: {lyrics_downloaded}")
        log.info("="*50)
        return lyrics_downloaded
    
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
        self, playlist_uuid: str, limit: int = Limits.PLAYLIST_ITEMS, offset: int = 0
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
