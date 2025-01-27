from pydantic import BaseModel
from typing import Optional, List, Literal, Dict, Union

from .track import Track
from .resource import Playlist, Album, Video
from .api import Items


class SearchAlbum(Album):
    # TODO: remove the artist field instead of making it None
    artist: None = None


class Artist(BaseModel):

    class Role(BaseModel):
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

    class Mix(BaseModel):
        ARTIST_MIX: str

    id: int
    name: str
    artistTypes: Optional[List[Literal["ARTIST", "CONTRIBUTOR"]]] = None
    url: Optional[str] = None
    picture: Optional[str] = None
    selectedAlbumCoverFallback: Optional[str] = None
    popularity: Optional[int] = None
    artistRoles: Optional[List[Role]] = None
    mixes: Optional[Mix | Dict] = None


class Search(BaseModel):
    class Artists(Items):
        items: List[Artist]

    class Albums(Items):
        items: List[SearchAlbum]

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
    topHit: TopHit
