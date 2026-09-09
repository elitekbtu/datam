import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import RegisterRequest
from core.security import hash_password, verify_password


class AuthError(Exception):
    """Raised when credentials are rejected or a registration conflicts."""


class EmailAlreadyExists(AuthError):
    pass


class UsernameAlreadyExists(AuthError):
    pass


class InvalidCredentials(AuthError):
    pass


class InactiveUser(AuthError):
    pass


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(func.lower(User.email) == email.strip().lower())
    return await db.scalar(stmt)


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    stmt = select(User).where(func.lower(User.username) == username.strip().lower())
    return await db.scalar(stmt)


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    email = payload.email.strip().lower()
    username = payload.username.strip()

    stmt = select(User).where(
        or_(
            func.lower(User.email) == email,
            func.lower(User.username) == username.lower(),
        )
    )
    existing = await db.scalar(stmt)
    if existing is not None:
        if existing.email.lower() == email:
            raise EmailAlreadyExists("An account with this email already exists")
        raise UsernameAlreadyExists("This username is already taken")

    user = User(
        email=email,
        username=username,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(db, email)
    if user is None:
        verify_password(password, "$2b$12$" + "." * 53)
        raise InvalidCredentials("Incorrect email or password")

    if not verify_password(password, user.hashed_password):
        raise InvalidCredentials("Incorrect email or password")

    if not user.is_active:
        raise InactiveUser("This account is disabled")

    return user
