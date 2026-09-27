import secrets

from fastapi import Response

from core.config import settings

ACCESS_COOKIE = "datam_access"
REFRESH_COOKIE = "datam_refresh"
CSRF_COOKIE = "datam_csrf"
GUEST_COOKIE = "datam_guest"


def set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    common = {"httponly": True, "secure": settings.COOKIE_SECURE, "samesite": "lax"}
    response.set_cookie(
        ACCESS_COOKIE,
        access,
        max_age=settings.access_token_expire_seconds,
        path="/api",
        **common,
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        max_age=settings.refresh_token_expire_seconds,
        path="/api/auth",
        **common,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/api")
    response.delete_cookie(REFRESH_COOKIE, path="/api/auth")


def set_csrf_cookie(response: Response) -> str:
    token = secrets.token_urlsafe(32)
    response.set_cookie(
        CSRF_COOKIE,
        token,
        max_age=settings.refresh_token_expire_seconds,
        path="/",
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        httponly=False,
    )
    return token


def set_guest_cookie(response: Response, guest_id: str) -> None:
    response.set_cookie(
        GUEST_COOKIE,
        guest_id,
        max_age=90 * 24 * 60 * 60,
        path="/api",
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        httponly=True,
    )
