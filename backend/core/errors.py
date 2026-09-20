from typing import Final

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exception_handlers import http_exception_handler

from app.services.errors import (
    Conflict,
    InvalidRequest,
    NotFound,
    PermissionDenied,
    ServiceError,
    Unauthenticated,
)

UNAUTHORIZED_HEADERS: Final = {"WWW-Authenticate": "Bearer"}

#: Checked in order, so a subclass may sit above the family it belongs to.
ERROR_STATUS: Final[tuple[tuple[type[ServiceError], int], ...]] = (
    (NotFound, status.HTTP_404_NOT_FOUND),
    (Conflict, status.HTTP_409_CONFLICT),
    (PermissionDenied, status.HTTP_403_FORBIDDEN),
    (Unauthenticated, status.HTTP_401_UNAUTHORIZED),
    (InvalidRequest, status.HTTP_400_BAD_REQUEST),
)


def http_error(exc: ServiceError) -> HTTPException:
    """Translate a service failure into the response a client should see."""
    for error_type, status_code in ERROR_STATUS:
        if isinstance(exc, error_type):
            return HTTPException(
                status_code,
                str(exc),
                headers=(
                    UNAUTHORIZED_HEADERS
                    if status_code == status.HTTP_401_UNAUTHORIZED
                    else None
                ),
            )
    return HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


def register_error_handlers(app: FastAPI) -> None:
    """Let routes raise service errors instead of catching each one by hand."""

    @app.exception_handler(ServiceError)
    async def handle_service_error(request: Request, exc: ServiceError) -> Response:
        return await http_exception_handler(request, http_error(exc))
