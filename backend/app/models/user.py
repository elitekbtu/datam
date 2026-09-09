import uuid

from sqlalchemy import Boolean, Enum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin
from utils.enums import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            native_enum=False,
            length=16,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=UserRole.USER,
        server_default=UserRole.USER.value,
        nullable=False,
    )

    @property
    def is_admin(self) -> bool:
        return self.role is UserRole.ADMIN

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role.value!r}>"
