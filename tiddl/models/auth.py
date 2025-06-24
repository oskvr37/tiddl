from typing import Optional
from pydantic import BaseModel, field_validator


class AuthUser(BaseModel):
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

    @field_validator('birthday', mode='before')
    def fix_birthday(cls, v):
        #Se Tidal restituisce un int (ms dal 1970), lo trasformiamo in stringa prima che Pydantic tenti la validazione.
        if isinstance(v, int):
            return str(v)
        return v


class AuthResponse(BaseModel):
    user: AuthUser
    scope: str
    clientName: str
    token_type: str
    access_token: str
    expires_in: int
    user_id: int


class AuthResponseWithRefresh(AuthResponse):
    refresh_token: str


class AuthDeviceResponse(BaseModel):
    deviceCode: str
    userCode: str
    verificationUri: str
    verificationUriComplete: str
    expiresIn: int
    interval: int
