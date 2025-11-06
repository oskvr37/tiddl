from pathlib import Path
from mutagen.easymp4 import EasyMP4 as MutagenEasyMP4
from tiddl.core.api.models import Video


def add_video_metadata(path: Path, video: Video):
    mutagen = MutagenEasyMP4(path)

    mutagen.update(
        {
            "title": video.title,
            "artist": ";".join([artist.name.strip() for artist in video.artists]),
        }
    )

    if video.artist:
        mutagen["albumartist"] = video.artist.name

    if video.album:
        mutagen["album"] = video.album.title

    if video.streamStartDate:
        mutagen["date"] = str(video.streamStartDate)

    if video.trackNumber:
        mutagen["tracknumber"] = str(video.trackNumber)

    if video.volumeNumber:
        mutagen["discnumber"] = str(video.volumeNumber)

    mutagen.save(path)
