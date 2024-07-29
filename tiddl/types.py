from typing import TypedDict, Optional, List, Any, Literal


TrackQuality = Literal["LOW", "HIGH", "LOSSLESS", "HI_RES_LOSSLESS"]
TrackArg = Literal["low", "normal", "high", "master"]

class QualityDetails(TypedDict):
    name: str
    details: str
    arg: TrackArg


TRACK_QUALITY: dict[TrackQuality, QualityDetails] = {
    "LOW": {"name": "Low", "details": "96 kbps", "arg": "low"},
    "HIGH": {"name": "Low", "details": "320 kbps", "arg": "normal"},
    "LOSSLESS": {"name": "High", "details": "16-bit, 44.1 kHz", "arg": "high"},
    "HI_RES_LOSSLESS": {
        "name": "Max",
        "details": "Up to 24-bit, 192 kHz",
        "arg": "master",
    },
}


class DeviceAuthData(TypedDict):
    deviceCode: str
    userCode: str
    verificationUri: str
    verificationUriComplete: str
    expiresIn: int
    interval: int


class User(TypedDict):
    userId: int
    email: str
    countryCode: str
    fullName: Optional[str]
    firstName: Optional[str]
    lastName: Optional[str]
    nickname: Optional[str]
    username: str
    address: Optional[str]
    city: Optional[str]
    postalcode: Optional[str]
    usState: Optional[str]
    phoneNumber: Optional[str]
    birthday: Optional[str]
    channelId: int
    parentId: int
    acceptedEULA: bool
    created: int
    updated: int
    facebookUid: int
    appleUid: Optional[str]
    googleUid: Optional[str]
    accountLinkCreated: bool
    emailVerified: bool
    newUser: bool


class AuthResponse(TypedDict):
    scope: str
    user: User
    clientName: str
    token_type: str
    access_token: str
    expires_in: int
    user_id: int


class AuthResponseWithRefresh(AuthResponse):
    refresh_token: str


class Client(TypedDict):
    id: int
    name: str
    authorizedForOffline: bool
    authorizedForOfflineDate: Optional[str]


class SessionResponse(TypedDict):
    sessionId: str
    userId: int
    countryCode: str
    channelId: int
    partnerId: int
    client: Client


class Creator(TypedDict):
    id: int


class PlaylistItem(TypedDict):
    uuid: str
    title: str
    numberOfTracks: int
    numberOfVideos: int
    creator: Creator
    description: str
    duration: int
    lastUpdated: str
    created: str
    type: str
    publicPlaylist: bool
    url: str
    image: str
    popularity: int
    squareImage: str
    promotedArtists: List[Any]  # dont know yet the type
    lastItemAddedAt: str


class PlaylistResponse(TypedDict):
    limit: int
    offset: int
    totalNumberOfItems: int
    items: List[PlaylistItem]


ManifestMimeType = Literal["application/dash+xml", "application/vnd.tidal.bts"]


class TrackResponse(TypedDict):
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
    bitDepth: int
    sampleRate: int
