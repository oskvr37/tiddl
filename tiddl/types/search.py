from pydantic import BaseModel
from typing import Optional, List, Literal, Dict, Union

from tiddl.types.track import Track
from tiddl.types.api import Items, Playlist


class _ArtistRole(BaseModel):
    categoryId: int
    category: Literal[
        "Artist",
        "Songwriter",
        "Performer",
        "Producer",
        "Engineer",
        "Production team",
        "Misc",
    ]


class _ArtistMix(BaseModel):
    ARTIST_MIX: str


class Artist(BaseModel):
    id: int
    name: str
    artistTypes: Optional[List[Literal["ARTIST", "CONTRIBUTOR"]]] = None
    url: Optional[str] = None
    picture: Optional[str] = None
    selectedAlbumCoverFallback: Optional[str] = None
    popularity: Optional[int] = None
    artistRoles: Optional[List[_ArtistRole]] = None
    mixes: Optional[_ArtistMix | Dict] = None


class SearchAritsts(Items):
    items: List[Artist]


class ArtistSearchAlbum(BaseModel):
    id: int
    name: str
    type: Literal["MAIN", "FEATURED"]
    picture: str


class SearchAlbum(BaseModel):
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
    version: Optional[str] = None
    url: str
    cover: Optional[str] = None
    videoCover: Optional[str] = None
    explicit: bool
    upc: str
    popularity: int
    audioQuality: str
    audioModes: List[str]
    artists: List[ArtistSearchAlbum | Dict]


class SearchAlbums(Items):
    items: List[SearchAlbum]


class SearchPlaylists(Items):
    items: List[Playlist]


class SearchTracks(Items):
    items: List[Track]


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
    artists: List[Artist]
    album: Optional[str] = None


class SearchVideo(Items):
    items: List[Video]


class TopHit(BaseModel):
    value: Union[Artist, Track, Playlist, SearchAlbum]
    type: Literal["ARTISTS", "TRACKS", "PLAYLISTS", "ALBUMS"]


class Search(BaseModel):
    artists: SearchAritsts
    albums: SearchAlbums
    playlists: SearchPlaylists
    tracks: SearchTracks
    videos: SearchVideo
    topHit: TopHit
