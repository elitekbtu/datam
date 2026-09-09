from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services import auth as auth_service
from core.security import TokenError, bearer_scheme, get_subject
from database.session import get_db
from utils.enums import TokenType, UserRole

DbSession = Annotated[AsyncSession, Depends(get_db)]
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
]

UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers=UNAUTHORIZED_HEADERS,
    )


async def get_current_user_optional(
    db: DbSession, credentials: BearerCredentials
) -> User | None:
    if credentials is None or not credentials.credentials:
        return None
    try:
        user_id = get_subject(credentials.credentials, TokenType.ACCESS)
    except TokenError:
        return None
    user = await auth_service.get_user_by_id(db, user_id)
    return user if user is not None and user.is_active else None


async def get_current_user(db: DbSession, credentials: BearerCredentials) -> User:
    if credentials is None or not credentials.credentials:
        raise unauthorized("Not authenticated")

    if credentials.scheme.lower() != "bearer":
        raise unauthorized("Invalid authentication scheme")

    try:
        user_id = get_subject(credentials.credentials, TokenType.ACCESS)
    except TokenError as exc:
        raise unauthorized(str(exc)) from exc

    user = await auth_service.get_user_by_id(db, user_id)
    if user is None:
        raise unauthorized("User no longer exists")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="This account is disabled"
        )
    return user


def require_role(*roles: UserRole):
    async def dependency(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges",
            )
        return user

    return dependency


OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(require_role(UserRole.ADMIN))]
