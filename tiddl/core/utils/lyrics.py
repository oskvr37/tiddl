import re
from pathlib import Path
from logging import getLogger

from tiddl.core.api.models import AlbumItems
from tiddl.core.api import ApiError
from tiddl.core.utils.format import format_template

log = getLogger(__name__)


def download_album_lyrics(
    get_track_lyrics,
    album_items: AlbumItems,
    song_dir: Path,
    skip_existing: bool = True,
    lyrics_template: str = "{item.number:02d} - {item.title}",
) -> bool:
    """
    Download lyrics for tracks in an album as .lrc files
    
    Args:
        get_track_lyrics: Function to fetch lyrics for a track (api.get_track_lyrics)
        album_items: AlbumItems object containing tracks
        song_dir: Directory where lyrics files will be saved
        skip_existing: Skip download if .lrc file already exists
        lyrics_template: Template for lyrics filename formatting
        
    Returns:
        True if any lyrics were downloaded, False otherwise
    """
    
    lyrics_downloaded = False
    
    for item in album_items.items:
        track = item.item if hasattr(item, "item") else item
        
        if not hasattr(track, "trackNumber"):
            continue
        
        filename = format_template(
            template=lyrics_template,
            item=track,
            album=None,
            quality="",
            with_asterisk_ext=False,
        )
        
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        lrc_path = song_dir / f"{filename}.lrc"
        
        # Skip if file exists - BEFORE making any API call
        if skip_existing and lrc_path.exists():
            log.debug(f"Lyrics file already exists, skipping: {lrc_path.name}")
            continue
        
        try:
            lyrics = get_track_lyrics(track.id)
            
            if not lyrics.subtitles and not lyrics.lyrics:
                log.debug(f"No lyrics available for track: {track.title}")
                continue
            
            content = lyrics.subtitles if lyrics.subtitles else lyrics.lyrics
            
            if not content:
                log.debug(f"Empty lyrics content for track: {track.title}")
                continue
            
            # Convert plain lyrics to LRC format if needed
            if not lyrics.subtitles and lyrics.lyrics:
                lines = []
                for line in lyrics.lyrics.splitlines():
                    if line.strip():
                        lines.append(f"[00:00.00]{line}")
                content = "\n".join(lines)
            
            lrc_path.parent.mkdir(parents=True, exist_ok=True)
            with lrc_path.open("w", encoding="utf-8") as f:
                f.write(content)
            
            log.debug(f"Downloaded lyrics for: {track.title}")
            lyrics_downloaded = True
            
        except ApiError as e:
            # Handle API errors gracefully (404 = no lyrics available)
            if hasattr(e, 'status') and e.status == 404:
                log.debug(f"No lyrics available for track: {track.title}")
            else:
                log.debug(f"API error downloading lyrics for {track.title}: {e}")
            continue
        except Exception as e:
            log.debug(f"Could not download lyrics for {track.title}: {e}")
            continue
    
    return lyrics_downloaded