import logging

from requests import Session
from pydantic import BaseModel
from base64 import b64decode
from xml.etree.ElementTree import fromstring

from tiddl.types import TrackStream


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


def downloadTrackStream(stream: TrackStream) -> tuple[bytes, str]:
    """Download data from track stream and return it with file extension."""

    decoded_manifest = b64decode(stream.manifest).decode()

    match stream.manifestMimeType:
        case "application/vnd.tidal.bts":
            track_manifest = TrackManifest.model_validate_json(decoded_manifest)
            urls, codecs = track_manifest.urls, track_manifest.codecs

        case "application/dash+xml":
            urls, codecs = parseManifestXML(decoded_manifest)

    logger.debug((stream.trackId, stream.audioQuality, codecs, len(urls)))

    if codecs == "flac":
        file_extension = "flac"
    elif codecs.startswith("mp4"):
        file_extension = "m4a"
    else:
        raise ValueError(f"Unknown codecs: {codecs}")

    with Session() as s:
        stream_data = b""

        for url in urls:
            req = s.get(url)
            stream_data += req.content

    return stream_data, file_extension
