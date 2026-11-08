import secrets
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.routes import api_router
from core.config import settings
from core.cookies import CSRF_COOKIE
from core.errors import register_error_handlers

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def is_untrusted_origin(request: Request) -> bool:
    origin = request.headers.get("origin")
    if not origin or origin in settings.CORS_ORIGINS:
        return False
    return urlsplit(origin).netloc != request.headers.get("host")


def has_csrf_token(request: Request) -> bool:
    cookie = request.cookies.get(CSRF_COOKIE, "")
    header = request.headers.get("x-csrf-token", "")
    return bool(cookie) and secrets.compare_digest(cookie, header)


@app.middleware("http")
async def protect_cookie_writes(request: Request, call_next):
    """Double-submit CSRF check for every API write; auth lives in cookies."""
    is_api_write = (
        request.url.path.startswith(settings.API_PREFIX + "/")
        and request.method not in SAFE_METHODS
    )
    if is_api_write:
        if is_untrusted_origin(request):
            return JSONResponse({"detail": "Untrusted origin"}, status_code=403)
        if not has_csrf_token(request):
            return JSONResponse({"detail": "CSRF token required"}, status_code=403)
    return await call_next(request)


register_error_handlers(app)

settings.MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
app.mount(settings.MEDIA_URL, StaticFiles(directory=settings.MEDIA_ROOT), name="media")
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
