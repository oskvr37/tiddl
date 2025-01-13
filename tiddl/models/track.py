from pydantic import BaseModel
from typing import Optional, List, Dict, Literal, Optional


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


class _Artist(BaseModel):
    id: int
    name: str
    type: str
    picture: Optional[str] = None


class _Album(BaseModel):
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
    streamStartDate: Optional[str] = None
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
    audioQuality: str
    audioModes: List[str]
    mediaMetadata: Dict[str, List[str]]
    artist: Optional[_Artist] = None
    artists: List[_Artist]
    album: _Album
    mixes: Dict[str, str]

    # this is used only when downloading playlist
    playlistNumber: Optional[int] = None
