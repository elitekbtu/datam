"""Photos kept on this machine, served straight from ``settings.MEDIA_URL``."""

import uuid
from collections.abc import Iterable
from contextlib import suppress
from pathlib import Path
from typing import Final

from fastapi import UploadFile

from app.services.catalog.errors import ImageTooLarge, UnsupportedImageType
from core.config import settings

IMAGE_TYPES: Final = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/avif": ".avif",
    "image/gif": ".gif",
}
CHUNK_SIZE: Final = 64 * 1024


def url_of(relative: Path) -> str:
    return f"{settings.MEDIA_URL.rstrip('/')}/{relative.as_posix()}"


def path_of(url: str) -> Path | None:
    """The file behind a URL we issued ourselves, or None for a remote one."""
    prefix = f"{settings.MEDIA_URL.rstrip('/')}/"
    if not url.startswith(prefix):
        return None
    root = settings.MEDIA_ROOT.resolve()
    path = (root / url[len(prefix) :]).resolve()
    return path if path.is_relative_to(root) else None


async def save(upload: UploadFile, folder: str) -> str:
    """Stream an upload to disk and return the URL it is served at."""
    suffix = IMAGE_TYPES.get(upload.content_type or "")
    if suffix is None:
        raise UnsupportedImageType(f"Upload one of: {', '.join(sorted(IMAGE_TYPES))}")

    relative = Path(folder) / f"{uuid.uuid4().hex}{suffix}"
    target = settings.MEDIA_ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    try:
        with target.open("wb") as stored:
            while chunk := await upload.read(CHUNK_SIZE):
                written += len(chunk)
                if written > settings.MAX_UPLOAD_BYTES:
                    raise ImageTooLarge(
                        f"Keep the file under {settings.MAX_UPLOAD_BYTES // 1024**2} MB"
                    )
                stored.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return url_of(relative)


def discard(urls: Iterable[str]) -> None:
    """Delete the files we stored; photos pointing elsewhere are left alone."""
    for url in urls:
        path = path_of(url)
        if path is None:
            continue
        path.unlink(missing_ok=True)
        if path.parent != settings.MEDIA_ROOT.resolve():
            with suppress(OSError):
                path.parent.rmdir()
