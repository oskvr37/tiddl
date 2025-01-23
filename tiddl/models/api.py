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


class BaseVideoArtist(BaseModel):
    id: int
    name: str
    type: str
    picture: Optional[str] = None


class BaseVideoAlbum(BaseModel):
    id: int
    title: str
    cover: str
    vibrantColor: str
    videoCover: Optional[str] = None


class BaseVideo(BaseModel):
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
    artist: BaseVideoArtist
    artists: List[BaseVideoArtist]
    album: Optional[BaseVideoAlbum] = None


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


ItemType = Literal["track", "video"]


class VideoItem(BaseModel):
    item: BaseVideo
    type: ItemType = "video"


class TrackItem(BaseModel):
    item: Track
    type: ItemType = "track"


class AlbumItems(Items):
    items: List[Union[TrackItem, VideoItem]]


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


class PlaylistVideo(BaseVideo):
    dateAdded: str
    index: int
    itemUuid: str


class PlaylistVideoItem(BaseModel):
    item: PlaylistVideo
    type: ItemType = "video"
    cut: None


class PlaylistTrack(Track):
    dateAdded: str
    index: int
    itemUuid: str


class PlaylistTrackItem(BaseModel):
    item: PlaylistTrack
    type: ItemType = "track"
    cut: None


class PlaylistItems(Items):
    items: List[Union[PlaylistTrackItem, PlaylistVideoItem]]


class Favorites(BaseModel):
    PLAYLIST: List[str]
    ALBUM: List[str]
    VIDEO: List[str]
    TRACK: List[str]
    ARTIST: List[str]
