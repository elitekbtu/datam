"""Account changes reserved for administrators, who cannot lock themselves out."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import AdminUserUpdate
from app.services.user.errors import SelfActionForbidden
from app.services.user.service import users


def guard_self_edit(user: User, payload: AdminUserUpdate, actor: User) -> None:
    if user.id != actor.id:
        return
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("role", user.role) is not user.role:
        raise SelfActionForbidden("You cannot change your own role")
    if changes.get("is_active", user.is_active) is False:
        raise SelfActionForbidden("You cannot disable your own account")


async def update(
    db: AsyncSession, user: User, payload: AdminUserUpdate, *, actor: User
) -> User:
    guard_self_edit(user, payload, actor)
    return await users.update(db, user, payload)


async def delete(db: AsyncSession, user: User, *, actor: User) -> None:
    if user.id == actor.id:
        raise SelfActionForbidden("You cannot delete your own account")
    await users.delete(db, user)
