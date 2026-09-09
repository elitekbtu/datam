import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Final

import bcrypt
import jwt
from fastapi.security import HTTPBearer

from core.config import settings
from utils.enums import TokenType

BCRYPT_MAX_BYTES: Final = 72

bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="JWT access token issued by `/api/auth/login`.",
    auto_error=False,
)


class TokenError(Exception):
    """Raised when a token is malformed, expired, or of an unexpected type."""


def _encode_password(password: str) -> bytes:
    return password.encode("utf-8")[:BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_encode_password(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            _encode_password(plain_password), hashed_password.encode("utf-8")
        )
    except ValueError:
        return False


def _create_token(
    subject: str | uuid.UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type.value,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(
    subject: str | uuid.UUID,
    expires_delta: timedelta | None = None,
    **extra_claims: Any,
) -> str:
    return _create_token(
        subject,
        TokenType.ACCESS,
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims,
    )


def create_refresh_token(
    subject: str | uuid.UUID,
    expires_delta: timedelta | None = None,
    **extra_claims: Any,
) -> str:
    return _create_token(
        subject,
        TokenType.REFRESH,
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        extra_claims,
    )


def create_token_pair(subject: str | uuid.UUID) -> tuple[str, str]:
    return create_access_token(subject), create_refresh_token(subject)


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.PyJWTError as exc:
        raise TokenError("Could not validate credentials") from exc

    if expected_type is not None and payload.get("type") != expected_type:
        raise TokenError(f"Expected a token of type '{expected_type.value}'")
    return payload


def get_subject(token: str, expected_type: TokenType | None = None) -> uuid.UUID:
    payload = decode_token(token, expected_type)
    try:
        return uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise TokenError("Token subject is invalid") from exc
