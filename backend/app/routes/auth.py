from fastapi import APIRouter, status

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
from app.services.user import users
from core.config import settings
from core.dependencies import DbSession
from core.security import create_token_pair

router = APIRouter(prefix="/auth", tags=["Auth"])


def token_pair(user: User) -> TokenPair:
    access_token, refresh_token = create_token_pair(user.id)
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_seconds,
    )


def auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        **token_pair(user).model_dump(),
        user=UserRead.model_validate(user),
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account and sign in",
)
async def register(payload: RegisterRequest, db: DbSession) -> AuthResponse:
    return auth_response(await users.create(db, payload))


@router.post(
    "/login", response_model=AuthResponse, summary="Exchange credentials for tokens"
)
async def login(payload: LoginRequest, db: DbSession) -> AuthResponse:
    user = await auth_service.authenticate(db, payload.email, payload.password)
    return auth_response(user)


@router.post(
    "/refresh", response_model=TokenPair, summary="Rotate an expiring access token"
)
async def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    user = await auth_service.from_refresh_token(db, payload.refresh_token)
    return token_pair(user)
