from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth.sessions import from_access
from app.services.base import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.services.errors import PermissionDenied, Unauthenticated
from core.cookies import ACCESS_COOKIE
from database.session import get_db
from utils.enums import UserRole

DbSession = Annotated[AsyncSession, Depends(get_db)]

@dataclass
class Pagination:
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE
    offset: Annotated[int, Query(ge=0)] = 0


async def get_current_user_optional(
    db: DbSession, request: Request
) -> User | None:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        return None
    try:
        return await from_access(db, token)
    except Unauthenticated:
        return None


async def get_current_user(db: DbSession, request: Request) -> User:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise Unauthenticated("Not authenticated")
    return await from_access(db, token)


def require_role(*roles: UserRole):
    async def dependency(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise PermissionDenied("Insufficient privileges")
        return user

    return dependency


require_admin = require_role(UserRole.ADMIN)

PageParams = Annotated[Pagination, Depends()]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(require_admin)]
