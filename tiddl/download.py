import logging
import requests
import json
import os
import ffmpeg

from queue import Queue
from threading import Thread
from time import time
from xml.etree.ElementTree import fromstring
from base64 import b64decode
from typing import TypedDict, List

from .types.track import ManifestMimeType

THREADS_COUNT = 4

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
        self.total = 0

    def download(self, urls: list[str]) -> bytes:
        self.total = len(urls)
        indexed_urls = [(i, url) for (i, url) in enumerate(urls)]
        threader = Threader(THREADS_COUNT, self._downloadFragment, indexed_urls)
        threader.run()
        sorted_content = sorted(self.indexed_content, key=lambda x: x[0])
        data = b"".join(content for _, content in sorted_content)
        return data

    def _downloadFragment(self, arg: tuple[int, str]):
        index, url = arg
        req = self.session.get(url)
        self.indexed_content.append((index, req.content))
        showProgressBar(
            len(self.indexed_content), self.total, "threaded download", show_size=False
        )


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


def showProgressBar(iteration: int, total: int, text: str, length=30, show_size=True):
    SQUARE, SQUARE_FILL = "□", "■"
    iteration_mb = iteration / 1024 / 1024
    total_mb = total / 1024 / 1024
    percent = 100 * (iteration / total)
    progress = int(length * iteration // total)
    bar = f"{SQUARE_FILL * progress}{SQUARE * (length - progress)}"
    size = f" {iteration_mb:.2f} / {total_mb:.2f} MB" if show_size else ""
    print(
        f"\r{text} {bar} {percent:.0f}%{size}",
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


def toFlac(track_data: bytes) -> bytes:
    process = (
        ffmpeg.input("pipe:0")
        .output("pipe:1", format="flac", codec="copy")
        .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
    )

    flac_data, stderr = process.communicate(input=track_data)

    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")

    return flac_data


def downloadTrackStream(
    encoded_manifest: str,
    mime_type: ManifestMimeType,
) -> tuple[bytes, str]:
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
        track_data = toFlac(track_data)

    """
    known codecs
        flac (master)
        mp4a.40.2 (high)
        mp4a.40.5 (low)
    """

    if codecs is None:
        raise Exception("Missing codecs")

    extension = "flac"

    if codecs.startswith("mp4a"):
        extension = "m4a"
    elif codecs != "flac":
        logger.warning(
            f'unknown file codecs: "{codecs}", please submit this as issue on GitHub'
        )

    return track_data, extension


def downloadCover(uid: str, path: str, size=1280):
    file = f"{path}/cover.jpg"

    if os.path.isfile(file):
        logger.debug(f"cover already exists ({file})")
        return

    formatted_uid = uid.replace("-", "/")
    url = f"https://resources.tidal.com/images/{formatted_uid}/{size}x{size}.jpg"

    req = requests.get(url)

    if req.status_code != 200:
        logger.error(f"could not download cover. ({req.status_code}) {url}")
        return

    try:
        with open(file, "wb") as f:
            f.write(req.content)
    except FileNotFoundError as e:
        logger.error(f"could not save cover. {file} -> {e}")


class Cover:
    def __init__(self, uid: str, size=1280) -> None:
        if size > 1280:
            logger.warning(
                f"can not set cover size higher than 1280 (user set: {size})"
            )
            size = 1280

        self.uid = uid

        formatted_uid = uid.replace("-", "/")
        self.url = (
            f"https://resources.tidal.com/images/{formatted_uid}/{size}x{size}.jpg"
        )

        logger.debug((self.uid, self.url))
        self.content = self.get()

    def get(self) -> bytes:
        req = requests.get(self.url)

        if req.status_code != 200:
            logger.error(f"could not download cover. ({req.status_code}) {self.url}")
            return b""

        logger.debug("got cover")

        return req.content

    def save(self, path: str):
        if not self.content:
            logger.error("cover file content is empty")
            return

        file = f"{path}/cover.jpg"

        if os.path.isfile(file):
            logger.debug(f"cover already exists ({file})")
            return

        try:
            with open(file, "wb") as f:
                logger.debug(file)
                f.write(self.content)
        except FileNotFoundError as e:
            logger.error(f"could not save cover. {file} -> {e}")
