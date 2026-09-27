import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import AuthSession
from app.models.user import User
from app.services.auth import ensure_active
from app.services.errors import Unauthenticated
from app.services.user import users
from core.config import settings
from core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from utils.enums import TokenType


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def pair(user_id: uuid.UUID, session_id: uuid.UUID) -> tuple[str, str]:
    claims = {"sid": str(session_id)}
    return create_access_token(user_id, **claims), create_refresh_token(
        user_id, **claims
    )


async def issue(db: AsyncSession, user: User) -> tuple[str, str]:
    session_id = uuid.uuid4()
    access, refresh = pair(user.id, session_id)
    db.add(
        AuthSession(
            id=session_id,
            user_id=user.id,
            refresh_hash=digest(refresh),
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    await db.commit()
    return access, refresh


async def rotate(db: AsyncSession, token: str) -> tuple[User, str, str]:
    try:
        payload = decode_token(token, TokenType.REFRESH)
        user_id = uuid.UUID(payload["sub"])
        session_id = uuid.UUID(payload["sid"])
    except (TokenError, KeyError, ValueError) as exc:
        raise Unauthenticated("Invalid refresh session") from exc
    user = await users.get(db, user_id)
    if user is None:
        raise Unauthenticated("User no longer exists")
    ensure_active(user)
    access, refresh = pair(user_id, session_id)
    changed = await db.execute(
        update(AuthSession)
        .where(
            AuthSession.id == session_id,
            AuthSession.user_id == user_id,
            AuthSession.refresh_hash == digest(token),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.now(UTC),
        )
        .values(
            refresh_hash=digest(refresh),
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    if changed.rowcount != 1:
        await db.rollback()
        raise Unauthenticated("Refresh session is no longer valid")
    await db.commit()
    return user, access, refresh


async def from_access(db: AsyncSession, token: str) -> User:
    try:
        payload = decode_token(token, TokenType.ACCESS)
        user_id = uuid.UUID(payload["sub"])
        session_id = uuid.UUID(payload["sid"])
    except (TokenError, KeyError, ValueError) as exc:
        raise Unauthenticated("Not authenticated") from exc
    active = await db.scalar(
        select(AuthSession.id).where(
            AuthSession.id == session_id,
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.now(UTC),
        )
    )
    if active is None:
        raise Unauthenticated("Session has expired")
    user = await users.get(db, user_id)
    if user is None:
        raise Unauthenticated("User no longer exists")
    return ensure_active(user)


async def revoke(db: AsyncSession, refresh_token: str | None) -> None:
    if not refresh_token:
        return
    try:
        payload = decode_token(refresh_token, TokenType.REFRESH)
        session_id = uuid.UUID(payload["sid"])
    except (TokenError, KeyError, ValueError):
        return
    await db.execute(
        update(AuthSession)
        .where(AuthSession.id == session_id)
        .values(revoked_at=datetime.now(UTC))
    )
    await db.commit()


async def revoke_all(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    await db.commit()
