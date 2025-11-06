from requests import Session

from tiddl.core.api.models import TrackStream, VideoStream
from .parse import parse_track_stream, parse_video_stream


def download(urls: list[str]) -> bytes:
    with Session() as s:
        stream_data = b""

        for url in urls:
            req = s.get(url)
            stream_data += req.content

    return stream_data


def get_track_stream_data(track_stream: TrackStream) -> tuple[bytes, str]:
    """Download data from track stream and return it with file extension."""

    urls, file_extension = parse_track_stream(track_stream)

    stream_data = download(urls)

    return stream_data, file_extension


def get_video_stream_data(video_stream: VideoStream) -> bytes:
    """Download data from video stream"""

    # there can be issue with memory.
    # currently we are loading data into ram
    # instead of writing it to file right away.

    urls = parse_video_stream(video_stream)

    stream_data = download(urls)

    return stream_data
