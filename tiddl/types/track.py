from typing import TypedDict, Optional, List, Dict, Literal, Optional


TrackQuality = Literal["LOW", "HIGH", "LOSSLESS", "HI_RES_LOSSLESS"]
ManifestMimeType = Literal["application/dash+xml", "application/vnd.tidal.bts"]


class TrackStream(TypedDict):
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
    bitDepth: Optional[int]
    sampleRate: Optional[int]


class _Artist(TypedDict):
    id: int
    name: str
    type: str
    picture: Optional[str]


class _Album(TypedDict):
    id: int
    title: str
    cover: str
    vibrantColor: str
    videoCover: Optional[str]


class Track(TypedDict):
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
    streamStartDate: str
    premiumStreamingOnly: bool
    trackNumber: int
    volumeNumber: int
    version: Optional[str]
    popularity: int
    copyright: str
    bpm: Optional[int]
    url: str
    isrc: str
    editable: bool
    explicit: bool
    audioQuality: str
    audioModes: List[str]
    mediaMetadata: Dict[str, List[str]]
    artist: _Artist
    artists: List[_Artist]
    album: _Album
    mixes: Dict[str, str]

    # this is used only when downloading playlist
    playlistNumber: Optional[int]
