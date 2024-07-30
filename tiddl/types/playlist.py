from typing import TypedDict, List, Any


class _Creator(TypedDict):
    id: int


class Playlist(TypedDict):
    uuid: str
    title: str
    numberOfTracks: int
    numberOfVideos: int
    creator: _Creator
    description: str
    duration: int
    lastUpdated: str
    created: str
    type: str
    publicPlaylist: bool
    url: str
    image: str
    popularity: int
    squareImage: str
    promotedArtists: List[Any]  # dont know yet the type
    lastItemAddedAt: str


class PlaylistResponse(TypedDict):
    limit: int
    offset: int
    totalNumberOfItems: int
    items: List[Playlist]
