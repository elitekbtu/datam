from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth import ensure_active
from app.services.base import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.services.errors import PermissionDenied, Unauthenticated
from app.services.user import users
from core.security import TokenError, bearer_scheme, get_subject
from database.session import get_db
from utils.enums import TokenType, UserRole

DbSession = Annotated[AsyncSession, Depends(get_db)]
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
]


@dataclass
class Pagination:
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE
    offset: Annotated[int, Query(ge=0)] = 0


async def get_current_user_optional(
    db: DbSession, credentials: BearerCredentials
) -> User | None:
    if credentials is None or not credentials.credentials:
        return None
    try:
        user_id = get_subject(credentials.credentials, TokenType.ACCESS)
    except TokenError:
        return None
    user = await users.get(db, user_id)
    return user if user is not None and user.is_active else None


async def get_current_user(db: DbSession, credentials: BearerCredentials) -> User:
    if credentials is None or not credentials.credentials:
        raise Unauthenticated("Not authenticated")

    try:
        user_id = get_subject(credentials.credentials, TokenType.ACCESS)
    except TokenError as exc:
        raise Unauthenticated(str(exc)) from exc

    user = await users.get(db, user_id)
    if user is None:
        raise Unauthenticated("User no longer exists")
    return ensure_active(user)


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
