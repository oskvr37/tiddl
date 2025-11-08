from pydantic import BaseModel
from urllib.parse import urlparse

from typing import Literal, get_args


ResourceTypeLiteral = Literal["track", "video", "album", "playlist", "artist", "mix"]


class TidalResource(BaseModel):
    type: ResourceTypeLiteral
    id: str

    @property
    def url(self) -> str:
        return f"https://listen.tidal.com/{self.type}/{self.id}"

    @classmethod
    def from_string(cls, string: str):
        """
        Extracts the resource type (e.g., "track", "album")
        and resource ID from a given input string.

        The input string can either be a full URL or a shorthand string
        in the format `resource_type/resource_id` (e.g., `track/12345678`).
        """

        path = urlparse(string).path
        resource_type, resource_id = path.split("/")[-2:]

        if resource_type not in get_args(ResourceTypeLiteral):
            raise ValueError(f"Invalid resource type: {resource_type}")

        digit_resource_types: list[ResourceTypeLiteral] = [
            "track",
            "album",
            "video",
            "artist",
        ]

        if resource_type in digit_resource_types and not resource_id.isdigit():
            raise ValueError(f"Invalid resource id: {resource_id}")

        return cls(type=resource_type, id=resource_id)  # type: ignore

    def __str__(self) -> str:
        return f"{self.type}/{self.id}"
