from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Literal, Dict, Union

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


class AlbumArtist(BaseModel):
    id: int
    name: str
    type: Literal["MAIN", "FEATURED"]


class Album(BaseModel):
    id: int
    title: str
    duration: int
    streamReady: bool
    streamStartDate: Optional[datetime] = None
    allowStreaming: bool
    premiumStreamingOnly: bool
    numberOfTracks: int
    numberOfVideos: int
    numberOfVolumes: int
    releaseDate: str
    copyright: str
    type: str
    version: Optional[str] = None
    url: str
    cover: Optional[str] = None
    videoCover: Optional[str] = None
    explicit: bool
    upc: str
    popularity: int
    audioQuality: str
    audioModes: List[str]
    artist: AlbumArtist
    artists: List[AlbumArtist]


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
    creator: _Creator | Dict
    description: Optional[str] = None
    duration: int
    lastUpdated: str
    created: str
    type: str
    publicPlaylist: bool
    url: str
    image: Optional[str] = None
    popularity: int
    squareImage: str
    promotedArtists: List[AlbumArtist]
    lastItemAddedAt: Optional[str] = None


class VideoArtist(BaseModel):
    id: int
    name: str
    type: str
    picture: str


class Video(BaseModel):
    id: int
    title: str
    volumeNumber: int
    trackNumber: int
    releaseDate: str
    imagePath: Optional[str] = None
    imageId: str
    vibrantColor: str
    duration: int
    quality: str
    streamReady: bool
    adSupportedStreamReady: bool
    djReady: bool
    stemReady: bool
    streamStartDate: str
    allowStreaming: bool
    explicit: bool
    popularity: int
    type: str
    adsUrl: Optional[str] = None
    adsPrePaywallOnly: bool
    artist: VideoArtist
    artists: List[VideoArtist]
    album: Optional[str] = None
    dateAdded: str
    index: int
    itemUuid: str


class _PlaylistItem(BaseModel):
    item: Union[Track, Video]
    type: Literal["track", "video"]
    cut: Literal[None]


class PlaylistItems(Items):
    items: List[_PlaylistItem]


class Favorites(BaseModel):
    PLAYLIST: List[str]
    ALBUM: List[str]
    VIDEO: List[str]
    TRACK: List[str]
    ARTIST: List[str]
