from urllib.parse import urlparse
from typing import Literal, get_args


ResourceTypeLiteral = Literal["track", "album", "playlist", "artist"]


class TidalResource:
    """
    A parser for Tidal resource URLs or strings.

    Extracts the resource type (e.g., "track", "album") and resource ID
    from a given input string. The input string can either be a full URL or a
    shorthand string in the format "resource_type/resource_id" (e.g., "track/12345678").
    """

    resource: str
    resource_type: ResourceTypeLiteral
    resource_id: str
    url: str

    def __init__(self, resource: str) -> None:
        self.resource = resource

        path = urlparse(self.resource).path
        resource_type, resource_id = path.split("/")[-2:]

        if resource_type not in get_args(ResourceTypeLiteral):
            raise ValueError(f"Invalid resource type: {resource_type}")

        self.resource_type = resource_type  # type: ignore

        if not resource_id.isdigit() and self.resource_type != "playlist":
            raise ValueError(f"Invalid resource id: {resource_id}")

        self.resource_id = resource_id

        self.url = f"https://listen.tidal.com/{self.resource_type}/{self.resource_id}"

    def __str__(self) -> str:
        return f"{self.resource_type}/{self.resource_id}"
