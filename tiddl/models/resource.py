from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Literal, Dict


class Video(BaseModel):

    class Arist(BaseModel):
        id: int
        name: str
        type: str
        picture: Optional[str] = None

    class Album(BaseModel):
        id: int
        title: str
        cover: str
        vibrantColor: str
        videoCover: Optional[str] = None

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
    artist: Arist
    artists: List[Arist]
    album: Optional[Album] = None


class Album(BaseModel):

    class Artist(BaseModel):
        id: int
        name: str
        type: Literal["MAIN", "FEATURED"]

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
    artist: Artist
    artists: List[Artist]


class Playlist(BaseModel):

    class Creator(BaseModel):
        id: int

    uuid: str
    title: str
    numberOfTracks: int
    numberOfVideos: int
    creator: Creator | Dict
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
    promotedArtists: List[Album.Artist]
    lastItemAddedAt: Optional[str] = None
