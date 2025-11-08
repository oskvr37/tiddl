from pydantic import BaseModel


class AuthData(BaseModel):
    token: str | None = None
    refresh_token: str | None = None
    expires_at: int = 0
    user_id: str | None = None
    country_code: str | None = None
