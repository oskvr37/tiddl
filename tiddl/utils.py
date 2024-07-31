from typing import Literal, List, get_args

RESOURCE = Literal["track", "album", "artist", "playlist"]
RESOURCE_LIST: List[RESOURCE] = list(get_args(RESOURCE))


def parseURL(url: str) -> tuple[RESOURCE, str]:
    # remove trailing slash
    url = url.rstrip("/")
    # remove params
    url = url.split("?")[0]

    fragments = url.split("/")

    if len(fragments) < 2:
        raise ValueError(f"Invalid input: {url}")

    parsed_type, parsed_id = fragments[-2], fragments[-1]

    if parsed_type not in RESOURCE_LIST:
        raise ValueError(f"Invalid resource type: {parsed_type} ({url})")

    return parsed_type, parsed_id


