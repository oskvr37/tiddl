from typing import TypedDict, Optional, List, Literal

from .track import Track


class ErrorResponse(TypedDict):
    status: int
    subStatus: int
    userMessage: str


class Client(TypedDict):
    id: int
    name: str
    authorizedForOffline: bool
    authorizedForOfflineDate: Optional[str]


class SessionResponse(TypedDict):
    sessionId: str
    userId: int
    countryCode: str
    channelId: int
    partnerId: int
    client: Client


class Items(TypedDict):
    limit: int
    offset: int
    totalNumberOfItems: int


class ArtistAlbum(TypedDict):
    id: int
    name: str
    type: Literal["MAIN"]


class Album(TypedDict):
    id: int
    title: str
    duration: int
    streamReady: bool
    streamStartDate: str
    allowStreaming: bool
    premiumStreamingOnly: bool
    numberOfTracks: int
    numberOfVideos: int
    numberOfVolumes: int
    releaseDate: str
    copyright: str
    type: str
    version: Optional[str]
    url: str
    cover: str
    videoCover: Optional[str]
    explicit: bool
    upc: str
    popularity: int
    audioQuality: str
    audioModes: List[str]
    artist: ArtistAlbum
    artists: List[ArtistAlbum]


class AristAlbumsItems(Items):
    items: List[Album]


class _AlbumTrack(TypedDict):
    item: Track
    type: Literal["track"]


class AlbumItems(Items):
    items: List[_AlbumTrack]


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
    promotedArtists: List[ArtistAlbum]
    lastItemAddedAt: str


class _PlaylistItem(TypedDict):
    item: Track
    type: Literal["track"]
    cut: Literal[None]


class PlaylistItems(Items):
    items: _PlaylistItem
