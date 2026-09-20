from fastapi import APIRouter

from app.routes.admin.catalog import catalog_router
from app.routes.admin.user import router as user_router

admin_router = APIRouter(prefix="/admin")
admin_router.include_router(user_router)
admin_router.include_router(catalog_router)

__all__ = ["admin_router"]
