from fastapi import APIRouter

from app.routes.account import router as account_router
from app.routes.admin import admin_router
from app.routes.auth import router as auth_router
from app.routes.catalog import catalog_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(account_router)
api_router.include_router(catalog_router)
api_router.include_router(admin_router)

__all__ = ["api_router"]
