"""What an account holder may change on their own account."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import PasswordChange
from app.services.user.errors import InvalidPassword, PasswordReuse
from app.services.user.service import users
from core.security import hash_password, verify_password


async def change_password(
    db: AsyncSession, user: User, payload: PasswordChange
) -> User:
    if not verify_password(payload.current_password, user.hashed_password):
        raise InvalidPassword("Current password is incorrect")
    if verify_password(payload.new_password, user.hashed_password):
        raise PasswordReuse("New password must differ from the current one")
    return await users.apply(
        db, user, {"hashed_password": hash_password(payload.new_password)}
    )


async def deactivate(db: AsyncSession, user: User) -> User:
    return await users.apply(db, user, {"is_active": False})
