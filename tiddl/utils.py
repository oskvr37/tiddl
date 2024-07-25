import requests
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


def downloadTrack(track_id: int, urls: list[str]):
    # both mp3 and flac extensions work
    print("downloading...")
    filename = f"{track_id}.flac"
    with open(filename, "wb+") as f:
        progress = 0
        for url in urls:
            progress += 1
            req = requests.get(url)
            print(f"{round(progress / len(urls) * 100)}%")
            f.write(req.content)
    print(f"file saved as ./{filename}")
