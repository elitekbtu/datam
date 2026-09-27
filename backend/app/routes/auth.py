from fastapi import APIRouter, Request, Response, status

from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.user import UserRead
from app.services import auth as auth_service
from app.services.auth import sessions
from app.services.user import users
from core.cookies import (
    GUEST_COOKIE,
    REFRESH_COOKIE,
    clear_auth_cookies,
    set_auth_cookies,
    set_csrf_cookie,
)
from core.dependencies import DbSession, OptionalUser
from app.services.errors import Unauthenticated

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/csrf", summary="Issue a CSRF token for cookie-authenticated writes")
async def csrf(response: Response) -> dict[str, str]:
    return {"csrf_token": set_csrf_cookie(response)}


@router.post(
    "/session",
    response_model=UserRead | None,
    summary="Read or renew the browser session",
)
async def session(
    request: Request, response: Response, db: DbSession, user: OptionalUser
) -> UserRead | None:
    if user:
        return UserRead.model_validate(user)
    token = request.cookies.get(REFRESH_COOKIE)
    if token:
        try:
            user, access, refresh_token = await sessions.rotate(db, token)
            set_auth_cookies(response, access, refresh_token)
            return UserRead.model_validate(user)
        except Unauthenticated:
            clear_auth_cookies(response)
    return None


async def finish_login(
    db: DbSession, request: Request, response: Response, user
) -> UserRead:
    from app.services.commerce.guest import merge_guest

    access, refresh = await sessions.issue(db, user)
    set_auth_cookies(response, access, refresh)
    if guest_id := request.cookies.get(GUEST_COOKIE):
        await merge_guest(db, guest_id, user.id)
    return UserRead.model_validate(user)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest, db: DbSession, request: Request, response: Response
) -> UserRead:
    return await finish_login(db, request, response, await users.create(db, payload))


@router.post("/login", response_model=UserRead)
async def login(
    payload: LoginRequest, db: DbSession, request: Request, response: Response
) -> UserRead:
    user = await auth_service.authenticate(db, payload.email, payload.password)
    return await finish_login(db, request, response, user)


@router.post("/refresh", response_model=UserRead)
async def refresh(request: Request, response: Response, db: DbSession) -> UserRead:
    from app.services.errors import Unauthenticated

    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise Unauthenticated("No refresh session")
    user, access, refresh_token = await sessions.rotate(db, token)
    set_auth_cookies(response, access, refresh_token)
    return UserRead.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, db: DbSession) -> None:
    await sessions.revoke(db, request.cookies.get(REFRESH_COOKIE))
    clear_auth_cookies(response)
