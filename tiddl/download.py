import logging
import requests
import json
import os

from queue import Queue
from threading import Thread
from time import time
from xml.etree.ElementTree import fromstring
from base64 import b64decode
from typing import TypedDict, List

from .types.track import ManifestMimeType


WORKERS_COUNT = 4

logger = logging.getLogger("download")


class Worker(Thread):
    def __init__(self, queue: Queue, function):
        Thread.__init__(self)
        self.queue = queue
        self.function = function
        self.daemon = True
        self.start()

    def run(self):
        while True:
            arg = self.queue.get()
            self.function(arg)
            self.queue.task_done()


class Threader:
    def __init__(self, workers_num: int, target, args: list) -> None:
        self.queue = Queue()

        for arg in args:
            self.queue.put(arg)

        self.workers: list[Worker] = [
            Worker(self.queue, target) for _ in range(workers_num)
        ]

    def run(self):
        ts = time()
        self.queue.join()
        return round(time() - ts, 2)


class Downloader:
    def __init__(self) -> None:
        self.indexed_content: list[tuple[int, bytes]] = []
        self.session = requests.Session()

    def download(self, urls: list[str]) -> bytes:
        indexed_urls = [(i, url) for (i, url) in enumerate(urls)]
        threader = Threader(WORKERS_COUNT, self._downloadFragment, indexed_urls)
        threader.run()
        sorted_content = sorted(self.indexed_content, key=lambda x: x[0])
        data = b"".join(content for _, content in sorted_content)
        return data

    def _downloadFragment(self, arg: tuple[int, str]):
        index, url = arg
        req = self.session.get(url)
        self.indexed_content.append((index, req.content))


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
    dl = Downloader()
    data = dl.download(urls)

    return data


def downloadTrackStream(
    full_path: str,
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

    logger.debug(f"codecs: {codecs}")

    if len(track_urls) == 1:
        track_data = download(track_urls[0])
    else:
        track_data = threadDownload(track_urls)
        codecs = "mp4a"  # for tracks that have mulitple `mp4` fragments

    """
    known codecs
        flac (master)
        mp4a.40.2 (high)
        mp4a.40.5 (low)
    """

    # TODO: use proper file extension ✨

    # quick fix for file extension

    if codecs is None:
        raise Exception("Missing codecs")

    if codecs == "flac":
        extension = "flac"
    elif codecs.startswith("mp4a"):
        extension = "m4a"
    else:
        extension = "flac"
        logger.warning(
            f'unknown file codecs: "{codecs}", please submit this as issue on GitHub'
        )

    file_path = os.path.dirname(full_path)
    file_name = f"{full_path}.{extension}"
    logger.debug(f"file_path: {file_path}, file_name: {file_name}")

    os.makedirs(file_path, exist_ok=True)

    with open(file_name, "wb+") as f:
        f.write(track_data)

    return file_name
