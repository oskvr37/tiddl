from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Literal


TrackQuality = Literal["LOW", "HIGH", "LOSSLESS", "HI_RES_LOSSLESS"]
ManifestMimeType = Literal["application/dash+xml", "application/vnd.tidal.bts"]


class TrackStream(BaseModel):
    trackId: int
    assetPresentation: Literal["FULL"]
    audioMode: Literal["STEREO"]
    audioQuality: TrackQuality
    manifestMimeType: ManifestMimeType
    manifestHash: str
    manifest: str
    albumReplayGain: float
    albumPeakAmplitude: float
    trackReplayGain: float
    trackPeakAmplitude: float
    bitDepth: Optional[int] = None
    sampleRate: Optional[int] = None


class TrackArtist(BaseModel):
    id: int
    name: str
    type: str
    picture: Optional[str] = None


class TrackAlbum(BaseModel):
    id: int
    title: str
    cover: Optional[str] = None
    vibrantColor: Optional[str] = None
    videoCover: Optional[str] = None


class Track(BaseModel):
    id: int
    title: str
    duration: int
    replayGain: float
    peak: float
    allowStreaming: bool
    streamReady: bool
    adSupportedStreamReady: bool
    djReady: bool
    stemReady: bool
    streamStartDate: Optional[datetime] = None
    premiumStreamingOnly: bool
    trackNumber: int
    volumeNumber: int
    version: Optional[str] = None
    popularity: int
    copyright: str
    bpm: Optional[int] = None
    url: str
    isrc: str
    editable: bool
    explicit: bool
    audioQuality: TrackQuality
    audioModes: List[str]
    mediaMetadata: Dict[str, List[str]]
    # for real, artist can be None?
    artist: Optional[TrackArtist] = None
    artists: List[TrackArtist]
    album: TrackAlbum
    mixes: Dict[str, str]
    playlistNumber: Optional[int] = None
