import logging

from m3u8 import M3U8
from requests import Session
from pydantic import BaseModel
from base64 import b64decode
from xml.etree.ElementTree import fromstring

from tiddl.models.api import TrackStream, VideoStream


logger = logging.getLogger(__name__)


def parseManifestXML(xml_content: str):
    """
    Parses XML manifest file of the track.
    """

    NS = "{urn:mpeg:dash:schema:mpd:2011}"

    tree = fromstring(xml_content)

    representationElement = tree.find(
        f"{NS}Period/{NS}AdaptationSet/{NS}Representation"
    )
    if representationElement is None:
        raise ValueError("Representation element not found")

    codecs = representationElement.get("codecs", "")

    segmentElement = representationElement.find(f"{NS}SegmentTemplate")
    if segmentElement is None:
        raise ValueError("SegmentTemplate element not found")

    url_template = segmentElement.get("media")
    if url_template is None:
        raise ValueError("No `media` attribute in SegmentTemplate")

    timelineElements = segmentElement.findall(f"{NS}SegmentTimeline/{NS}S")
    if not timelineElements:
        raise ValueError("SegmentTimeline elements not found")

    total = 0
    for element in timelineElements:
        total += 1
        count = element.get("r")
        if count is not None:
            total += int(count)

    urls = [url_template.replace("$Number$", str(i)) for i in range(0, total + 1)]

    return urls, codecs


class TrackManifest(BaseModel):
    mimeType: str
    codecs: str
    encryptionType: str
    urls: list[str]


def parseTrackStream(track_stream: TrackStream) -> tuple[list[str], str]:
    """Parse URLs and file extension from `track_stream`"""

    decoded_manifest = b64decode(track_stream.manifest).decode()

    match track_stream.manifestMimeType:
        case "application/vnd.tidal.bts":
            track_manifest = TrackManifest.model_validate_json(decoded_manifest)
            urls, codecs = track_manifest.urls, track_manifest.codecs

        case "application/dash+xml":
            urls, codecs = parseManifestXML(decoded_manifest)

    if codecs == "flac":
        file_extension = ".flac"
        if track_stream.audioQuality == "HI_RES_LOSSLESS":
            file_extension = ".m4a"
    elif codecs.startswith("mp4"):
        file_extension = ".m4a"
    else:
        raise ValueError(
            f"Unknown codecs `{codecs}` (trackId {track_stream.trackId}"
        )

    return urls, file_extension


def downloadTrackStream(track_stream: TrackStream) -> tuple[bytes, str]:
    """Download data from track stream and return it with file extension."""

    urls, file_extension = parseTrackStream(track_stream)

    with Session() as s:
        stream_data = b""

        for url in urls:
            req = s.get(url)
            stream_data += req.content

    return stream_data, file_extension


def parseVideoStream(video_stream: VideoStream) -> list[str]:
    """Parse `video_stream` manifest and return video urls"""

    # TOOD: add video quality arg.
    # for now we download the highest quality

    class VideoManifest(BaseModel):
        mimeType: str
        urls: list[str]

    decoded_manifest = b64decode(video_stream.manifest).decode()
    manifest = VideoManifest.model_validate_json(decoded_manifest)

    with Session() as s:
        # get all qualities
        req = s.get(manifest.urls[0])
        m3u8 = M3U8(req.text)

        # get highest quality
        uri = m3u8.playlists[-1].uri

        if not uri:
            raise ValueError("M3U8 Playlist does not have `uri`.")

        req = s.get(uri)
        video = M3U8(req.text)

    if not video.files:
        raise ValueError("M3U8 Playlist is empty.")

    urls = [url for url in video.files if url]

    return urls
