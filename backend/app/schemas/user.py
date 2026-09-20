import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import Page, ReadSchema, WriteSchema
from utils.enums import UserRole

Email = Annotated[EmailStr, Field(examples=["user@example.com"])]
Username = Annotated[
    str, Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_.-]+$")
]
FullName = Annotated[str | None, Field(max_length=128)]
Password = Annotated[str, Field(min_length=8, max_length=72, examples=["s3cret-pass"])]


class UserBase(BaseModel):
    email: Email
    username: Username
    full_name: FullName = None


class UserRead(UserBase, ReadSchema):
    id: uuid.UUID
    is_active: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime


class UserCreate(UserBase, WriteSchema):
    password: Password


class AdminUserCreate(UserCreate):
    role: UserRole = UserRole.USER
    is_active: bool = True


class UserUpdate(WriteSchema):
    """Profile fields an account holder may change on their own."""

    email: Email | None = None
    username: Username | None = None
    full_name: FullName = None


class AdminUserUpdate(UserUpdate):
    """Everything an administrator may change on any account."""

    password: Password | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class PasswordChange(WriteSchema):
    current_password: Annotated[str, Field(min_length=1, max_length=72)]
    new_password: Password


UserPage = Page[UserRead]
