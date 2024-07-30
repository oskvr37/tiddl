from typing import TypedDict, Optional


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
