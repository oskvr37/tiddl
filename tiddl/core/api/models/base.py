from pydantic import BaseModel
from typing import Optional, List, Literal, Union

from .resources import Album, Artist, Playlist, Track, TrackQuality, Video, VideoQuality


class SessionResponse(BaseModel):
    class Client(BaseModel):
        id: int
        name: str
        authorizedForOffline: bool
        authorizedForOfflineDate: Optional[str]

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


class ArtistAlbumsItems(Items):
    items: List[Album]


class ArtistVideosItems(Items):
    items: List[Video]


ItemType = Literal["track", "video"]


class AlbumItems(Items):
    class VideoItem(BaseModel):
        item: Video
        type: ItemType = "video"

    class TrackItem(BaseModel):
        item: Track
        type: ItemType = "track"

    items: List[Union[TrackItem, VideoItem]]


class AlbumItemsCredits(Items):
    class ItemWithCredits(BaseModel):
        class CreditsEntry(BaseModel):
            class Contributor(BaseModel):
                name: str
                id: Optional[int] = None

            type: str
            contributors: List[Contributor]

        credits: List[CreditsEntry]

    class VideoItem(ItemWithCredits):
        item: Video
        type: ItemType = "video"

    class TrackItem(ItemWithCredits):
        item: Track
        type: ItemType = "track"

    items: List[Union[TrackItem, VideoItem]]


class PlaylistItems(Items):
    class PlaylistVideoItem(BaseModel):
        class PlaylistVideo(Video):
            dateAdded: str
            index: int
            itemUuid: str

        item: PlaylistVideo
        type: ItemType = "video"
        cut: None

    class PlaylistTrackItem(BaseModel):
        class PlaylistTrack(Track):
            dateAdded: str
            index: int
            itemUuid: str
            # playlist tracks albums have releasedate,
            # but tracks alone do not lol

        item: PlaylistTrack
        type: ItemType = "track"
        cut: None

    items: List[Union[PlaylistTrackItem, PlaylistVideoItem]]


class MixItems(Items):
    class MixItem(BaseModel):
        item: Track
        type: ItemType = "track"

    items: List[MixItem]


class Favorites(BaseModel):
    PLAYLIST: List[str]
    ALBUM: List[str]
    VIDEO: List[str]
    TRACK: List[str]
    ARTIST: List[str]


class TrackStream(BaseModel):
    trackId: int
    assetPresentation: Literal["FULL"]
    audioMode: Literal["STEREO"]
    audioQuality: TrackQuality
    manifestMimeType: Literal["application/dash+xml", "application/vnd.tidal.bts"]
    manifestHash: str
    manifest: str
    albumReplayGain: float
    albumPeakAmplitude: float
    trackReplayGain: float
    trackPeakAmplitude: float
    bitDepth: Optional[int] = None
    sampleRate: Optional[int] = None


class VideoStream(BaseModel):
    videoId: int
    streamType: Literal["ON_DEMAND"]
    assetPresentation: Literal["FULL"]
    videoQuality: VideoQuality
    # streamingSessionId: str  # only in web?
    manifestMimeType: Literal["application/dash+xml", "application/vnd.tidal.emu"]
    manifestHash: str
    manifest: str


class Search(BaseModel):

    class Artists(Items):
        items: List[Artist]

    class Albums(Items):
        items: List[Album]

    class Playlists(Items):
        items: List[Playlist]

    class Tracks(Items):
        items: List[Track]

    class Videos(Items):
        items: List[Video]

    class TopHit(BaseModel):
        value: Union[Artist, Track, Playlist, Album]
        type: Literal["ARTISTS", "TRACKS", "PLAYLISTS", "ALBUMS"]

    artists: Artists
    albums: Albums
    playlists: Playlists
    tracks: Tracks
    videos: Videos
    topHit: Optional[TopHit] = None


class TrackLyrics(BaseModel):
    isRightToLeft: bool
    lyrics: str
    lyricsProvider: str
    providerCommontrackId: str
    providerLyricsId: str
    subtitles: str
    trackId: int
