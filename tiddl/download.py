import logging
import requests
import json

from os import makedirs
from xml.etree.ElementTree import fromstring
from base64 import b64decode
from typing import TypedDict, List

from .types import ManifestMimeType


logger = logging.getLogger("download")


def decodeManifest(manifest: str):
    return b64decode(manifest).decode()


def parseManifest(manifest: str):
    class AudioFileInfo(TypedDict):
        mimeType: str
        codecs: str
        encryptionType: str
        urls: List[str]

    data: AudioFileInfo = json.loads(manifest)
    return data


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

    codecs = representationElement.get("codecs")

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


def threadDownload(urls: list[str]) -> bytes:
    # TODO: implement threaded download ⚡️
    # TODO: add progress bar ✨

    data = b""
    for index, url in enumerate(urls):
        req = requests.get(url)
        data += req.content
        print(f"{round((index + 1) / len(urls) * 100)}%")

    return data


def downloadTrack(
    path: str, file_name: str, encoded_manifest: str, mime_type: ManifestMimeType
):
    logger.debug(mime_type)
    manifest = decodeManifest(encoded_manifest)

    match mime_type:
        case "application/dash+xml":
            track_urls, codecs = parseManifestXML(manifest)
        case "application/vnd.tidal.bts":
            data = parseManifest(manifest)
            track_urls, codecs = data["urls"], data["codecs"]
        case _:
            raise ValueError(f"Unknown `mime_type`: {mime_type}")

    track_data = threadDownload(track_urls)

    logger.debug(codecs)

    """
    known codecs
        flac (master)
        mp4a.40.2 (high)
        mp4a.40.5 (low)
    """

    makedirs(path, exist_ok=True)

    # TODO: use proper file extension ✨
    file_path = f"{path}/{file_name}.flac"

    with open(file_path, "wb+") as f:
        f.write(track_data)

    return file_path
