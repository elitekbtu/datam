from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserBase, UserRead


class RegisterRequest(UserBase):
    password: str = Field(..., min_length=8, max_length=72, examples=["s3cret-pass"])


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=1, max_length=72, examples=["s3cret-pass"])


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(TokenPair):
    user: UserRead
