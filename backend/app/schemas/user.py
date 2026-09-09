import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from utils.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    username: str = Field(..., min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_.-]+$")
    full_name: str | None = Field(default=None, max_length=128)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime
