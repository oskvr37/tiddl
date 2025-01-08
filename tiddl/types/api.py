from pydantic import BaseModel
from typing import Optional, List, Literal

from .track import Track


class Client(BaseModel):
    id: int
    name: str
    authorizedForOffline: bool
    authorizedForOfflineDate: Optional[str]


class SessionResponse(BaseModel):
    sessionId: str
    userId: int
    countryCode: str
    channelId: int
    partnerId: int
    client: Client


class Items(BaseModel):
    limit: int
    offset: int
    totalNumberOfItems: int


class ArtistAlbum(BaseModel):
    id: int
    name: str
    type: Literal["MAIN", "FEATURED"]


class Album(BaseModel):
    id: int
    title: str
    duration: int
    streamReady: bool
    streamStartDate: Optional[str] = None
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
    cover: Optional[str] = None
    videoCover: Optional[str] = None
    explicit: bool
    upc: str
    popularity: int
    audioQuality: str
    audioModes: List[str]
    artist: ArtistAlbum
    artists: List[ArtistAlbum]


class AristAlbumsItems(Items):
    items: List[Album]


class _AlbumTrack(BaseModel):
    item: Track
    type: Literal["track"]


class AlbumItems(Items):
    items: List[_AlbumTrack]


class _Creator(BaseModel):
    id: int


class Playlist(BaseModel):
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


class _PlaylistItem(BaseModel):
    item: Track
    type: Literal["track"]
    cut: Literal[None]


class PlaylistItems(Items):
    items: List[_PlaylistItem]


class Favorites(BaseModel):
    PLAYLIST: List[str]
    ALBUM: List[str]
    VIDEO: List[str]
    TRACK: List[str]
    ARTIST: List[str]
