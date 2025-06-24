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
    Lyrics
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

        CACHE_NAME = "tiddl_api_cache"

        self.session = CachedSession(
            cache_name=HOME_PATH / CACHE_NAME, always_revalidate=omit_cache
        )
        self.session.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }


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

        try:
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

        finally:
            # Chiude la response
            try:
                req.close()
            except Exception:
                pass
            # Chiude la sessione
            try:
                self.session.close()
            except Exception:
                pass

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
                "limit": limit,
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

    def getLyrics(self, track_id: str | int):
        return self.fetch(
            Lyrics, f"tracks/{track_id}/lyrics", {"countryCode": self.country_code}
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

    # --- Nuovi metodi per copertine e testi ---
    def downloadAlbumCover(self, album_id: str | int, save_path: Path, skip_existing: bool = True) -> Path:
        """
        Scarica l'immagine di copertina di un album
        """
        # Check if cover already exists and skip if requested
        if skip_existing and save_path.exists():
            # Don't log here, let the caller handle the logging
            return save_path

        album = self.getAlbum(album_id)
        if not album.cover:
            raise ValueError(f"Album {album_id} has no cover")
        
        # Use the same cover URL format as the existing Cover class
        cover_id = album.cover.replace('-', '/')
        url = f"https://resources.tidal.com/images/{cover_id}/1280x1280.jpg"
        
        resp = self.session.get(url)
        resp.raise_for_status()
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with save_path.open('wb') as f:
            f.write(resp.content)
        
        resp.close()
        return save_path

    def downloadAlbumLyrics(self, album_id: str | int, song_dir: Path, filename_template: str = "{trackNumber:02d} - {title}.lrc", skip_existing: bool = True) -> bool:
        """
        Scarica i testi di tutte le tracce di un album, li formatta in LRC e li salva nella cartella delle canzoni
        song_dir: Path della cartella contenente le tracce audio
        filename_template: template per il nome file .lrc
        skip_existing: se True, salta i file .lrc già esistenti
        
        Returns: True if any lyrics were downloaded, False otherwise
        """
        lyrics_downloaded = False
        
        # Get album items with proper pagination
        offset = 0
        while True:
            album_items = self.getAlbumItems(album_id, offset=offset)
            
            for item in album_items.items:
                # Handle both TrackItem and VideoItem
                track = item.item if hasattr(item, 'item') else item
                
                # Skip if not a track
                if not hasattr(track, 'trackNumber'):
                    continue
                
                # Costruisci il path basato sul template
                filename = filename_template.format(
                    trackNumber=track.trackNumber,
                    title=self._sanitize_filename(track.title)
                )
                
                path = song_dir / filename
                
                # Check if lyrics file already exists and skip if requested
                if skip_existing and path.exists():
                    logging.warning(f"Lyrics '{track.title}' skipped")
                    continue
                    
                try:
                    lyrics = self.getLyrics(track.id)
                    if not lyrics.subtitles and not lyrics.lyrics:
                        logging.debug(f"No lyrics available for track: {track.title}")
                        continue
                    
                    # Use subtitles if available (they have timing), otherwise use plain lyrics
                    content = lyrics.subtitles if lyrics.subtitles else lyrics.lyrics
                    
                    if not content:
                        logging.debug(f"Empty lyrics content for track: {track.title}")
                        continue
                    
                    # If it's plain lyrics, convert to basic LRC format
                    if not lyrics.subtitles and lyrics.lyrics:
                        lines = []
                        for line in lyrics.lyrics.splitlines():
                            if line.strip():  # Skip empty lines
                                lines.append(f"[00:00.00]{line}")
                        content = "\n".join(lines)
                    
                    path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with path.open('w', encoding='utf-8') as f:
                        f.write(content)
                        
                    logging.info(f"Downloaded lyrics for track: {track.title}")
                    lyrics_downloaded = True
                    
                except Exception as e:
                    # Generic exception handling - this will catch ApiError and any other errors
                    logging.debug(f"Could not download lyrics for track {track.title}: {str(e)}")
                    continue
            
            # Check if we've got all items
            if album_items.limit + album_items.offset >= album_items.totalNumberOfItems:
                break
            
            offset += album_items.limit
        
        return lyrics_downloaded

    def _sanitize_filename(self, filename: str) -> str:
        """Remove or replace characters that are not allowed in filenames"""
        import re
        # Replace problematic characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        return filename.strip()

    def downloadAlbumAssets(self, album_id: str | int, base_dir: Path, skip_existing: bool = True) -> None:
        """
        Scarica copertina e testi LRC per un album
        I file LRC vengono salvati nella stessa cartella delle tracce
        skip_existing: se True, salta i file già esistenti
        """
        assets_downloaded = False
        
        try:
            # Download album cover
            cover_path = base_dir / 'cover.jpg'
            if not (skip_existing and cover_path.exists()):
                self.downloadAlbumCover(album_id, cover_path, skip_existing)
                logging.info(f"Downloaded album cover to: {cover_path}")
                assets_downloaded = True
            else:
                logging.warning(f"Album cover '{cover_path.name}' skipped")
        except Exception as e:
            logging.warning(f"Could not download album cover: {e}")
        
        try:
            # Download lyrics to the same directory where tracks will be saved
            lyrics_downloaded = self.downloadAlbumLyrics(album_id, base_dir, skip_existing=skip_existing)
            if lyrics_downloaded:
                assets_downloaded = True
        except Exception as e:
            logging.warning(f"Could not download album lyrics: {e}")
        
        # Only log success message if something was actually downloaded
        if assets_downloaded:
            album = self.getAlbum(album_id)
            logging.info(f"Downloaded album assets for {album.title}")