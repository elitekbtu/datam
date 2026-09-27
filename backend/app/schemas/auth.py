from app.schemas.base import WriteSchema
from app.schemas.user import Email, Password, UserCreate


class RegisterRequest(UserCreate):
    """Self-service signup; an administrator uses `AdminUserCreate` instead."""


class LoginRequest(WriteSchema):
    email: Email
    password: Password
