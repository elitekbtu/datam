from fastapi import APIRouter, HTTPException, status

from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.schemas.user import UserRead
from app.services import auth as auth_service
from core.config import settings
from core.dependencies import CurrentUser, DbSession
from core.settings import TokenError, create_token_pair, get_subject
from utils.enums import TokenType

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_pair(user: User) -> TokenPair:
    access_token, refresh_token = create_token_pair(user.id)
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_seconds,
    )


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        **_token_pair(user).model_dump(),
        user=UserRead.model_validate(user),
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account and sign in",
)
async def register(payload: RegisterRequest, db: DbSession) -> AuthResponse:
    try:
        user = await auth_service.register_user(db, payload)
    except auth_service.EmailAlreadyExists as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except auth_service.UsernameAlreadyExists as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse, summary="Exchange credentials for tokens")
async def login(payload: LoginRequest, db: DbSession) -> AuthResponse:
    try:
        user = await auth_service.authenticate_user(db, payload.email, payload.password)
    except auth_service.InvalidCredentials as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except auth_service.InactiveUser as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    return _auth_response(user)


@router.post("/refresh", response_model=TokenPair, summary="Rotate an expiring access token")
async def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    try:
        user_id = get_subject(payload.refresh_token, TokenType.REFRESH)
    except TokenError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await auth_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is disabled")

    return _token_pair(user)


@router.get("/me", response_model=UserRead, summary="Current authenticated user")
async def read_me(user: CurrentUser) -> User:
    return user
