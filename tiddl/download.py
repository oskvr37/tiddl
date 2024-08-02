import logging
import requests
import json
import os

from xml.etree.ElementTree import fromstring
from base64 import b64decode
from typing import TypedDict, List

from .types.track import ManifestMimeType


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


def showProgressBar(iteration: int, total: int, text: str, length=30):
    SQUARE, SQUARE_FILL = "□", "■"
    iteration_mb = iteration / 1024 / 1024
    total_mb = total / 1024 / 1024
    percent = 100 * (iteration / total)
    progress = int(length * iteration // total)
    bar = f"{SQUARE_FILL * progress}{SQUARE * (length - progress)}"
    print(
        f"\r{text} {bar} {percent:.0f}% {iteration_mb:.2f} / {total_mb:.2f} MB",
        end="\r",
    )
    if iteration >= total:
        print()


def download(url: str) -> bytes:
    logger.debug(url)
    # use session for performance
    session = requests.Session()
    req = session.get(url, stream=True)
    total_size = int(req.headers.get("content-length", 0))
    block_size = 1024 * 1024
    data = b""

    for block in req.iter_content(block_size):
        data += block
        showProgressBar(len(data), total_size, "Single URL")

    return data


def threadDownload(urls: list[str]) -> bytes:
    # TODO: implement threaded download ⚡️
    data = b""
    for index, url in enumerate(urls):
        req = requests.get(url)
        data += req.content
        showProgressBar(index, len(urls), f"{len(urls)} URLs")

    return data


def downloadTrackStream(
    download_path: str,
    file_name: str,
    encoded_manifest: str,
    mime_type: ManifestMimeType,
):
    logger.debug(f"mime_type: {mime_type}")
    manifest = decodeManifest(encoded_manifest)

    match mime_type:
        case "application/dash+xml":
            track_urls, codecs = parseManifestXML(manifest)
        case "application/vnd.tidal.bts":
            data = parseManifest(manifest)
            track_urls, codecs = data["urls"], data["codecs"]
        case _:
            raise ValueError(f"Unknown `mime_type`: {mime_type}")

    if len(track_urls) == 1:
        track_data = download(track_urls[0])
    else:
        track_data = threadDownload(track_urls)

    logger.debug(f"codecs: {codecs}")

    """
    known codecs
        flac (master)
        mp4a.40.2 (high)
        mp4a.40.5 (low)
    """

    # TODO: use proper file extension ✨
    file_path = f"{download_path}/{file_name}.flac"

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb+") as f:
        f.write(track_data)

    return file_path
