from pydantic import BaseModel

from app.schemas.base import WriteSchema
from app.schemas.user import Email, Password, UserCreate, UserRead


class RegisterRequest(UserCreate):
    """Self-service signup; an administrator uses `AdminUserCreate` instead."""


class LoginRequest(WriteSchema):
    email: Email
    password: Password


class RefreshRequest(WriteSchema):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(TokenPair):
    user: UserRead
