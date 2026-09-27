import secrets
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import api_router
from core.config import settings
from core.cookies import CSRF_COOKIE
from core.errors import register_error_handlers

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def protect_cookie_writes(request: Request, call_next):
    if request.url.path.startswith(settings.API_PREFIX + "/") and request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin and urlsplit(origin).netloc != request.headers.get("host") and origin not in settings.CORS_ORIGINS:
            return JSONResponse({"detail": "Untrusted origin"}, status_code=403)
        cookie = request.cookies.get(CSRF_COOKIE, "")
        header = request.headers.get("x-csrf-token", "")
        if not cookie or not secrets.compare_digest(cookie, header):
            return JSONResponse({"detail": "CSRF token required"}, status_code=403)
    return await call_next(request)

register_error_handlers(app)

settings.MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
app.mount(
    settings.MEDIA_URL,
    StaticFiles(directory=settings.MEDIA_ROOT),
    name="media",
)

app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
