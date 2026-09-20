"""Turns credentials and refresh tokens into the account behind them."""

from typing import Final

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth.errors import InactiveUser, InvalidCredentials
from app.services.user import users
from core.security import TokenError, get_subject, verify_password
from utils.enums import TokenType

DUMMY_HASH: Final = "$2b$12$" + "." * 53


def ensure_active(user: User) -> User:
    if not user.is_active:
        raise InactiveUser("This account is disabled")
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = await users.by_email(db, email)
    if user is None:
        verify_password(password, DUMMY_HASH)
        raise InvalidCredentials("Incorrect email or password")
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentials("Incorrect email or password")
    return ensure_active(user)


async def from_refresh_token(db: AsyncSession, token: str) -> User:
    try:
        user_id = get_subject(token, TokenType.REFRESH)
    except TokenError as exc:
        raise InvalidCredentials(str(exc)) from exc

    user = await users.get(db, user_id)
    if user is None:
        raise InvalidCredentials("User no longer exists")
    return ensure_active(user)
