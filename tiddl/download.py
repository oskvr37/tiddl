import requests
from os import makedirs
from xml.etree.ElementTree import fromstring
from base64 import b64decode


def decodeManifest(manifest: str):
    return b64decode(manifest).decode()


def parseTrackManifest(xml_content: str):
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

    data = b""
    for index, url in enumerate(urls):
        req = requests.get(url)
        data += req.content
        print(f"{round(index / len(urls) * 100)}%")

    return data


def downloadTrack(file_name: int, manifest: str, path: str):
    decoded_manifest = decodeManifest(manifest)
    track_urls, codecs = parseTrackManifest(decoded_manifest)
    track_data = threadDownload(track_urls)

    makedirs(path, exist_ok=True)

    # TODO: use proper file extension ✨
    file_path = f"{path}/{file_name}.flac"

    with open(file_path, "wb+") as f:
        f.write(track_data)

    return file_path
