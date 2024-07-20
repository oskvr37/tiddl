from typing import TypedDict, Optional


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


class AuthData(TypedDict):
    scope: str
    user: User
    clientName: str
    token_type: str
    access_token: str
    refresh_token: str
    expires_in: int
    user_id: int
