from pydantic import BaseModel
from typing import Optional, List, Literal, Union

from .track import Track
from .resource import Video, Album


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


class AristAlbumsItems(Items):
    items: List[Album]


ItemType = Literal["track", "video"]


class AlbumItems(Items):

    class VideoItem(BaseModel):
        item: Video
        type: ItemType = "video"

    class TrackItem(BaseModel):
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

        item: PlaylistTrack
        type: ItemType = "track"
        cut: None

    items: List[Union[PlaylistTrackItem, PlaylistVideoItem]]


class Favorites(BaseModel):
    PLAYLIST: List[str]
    ALBUM: List[str]
    VIDEO: List[str]
    TRACK: List[str]
    ARTIST: List[str]
