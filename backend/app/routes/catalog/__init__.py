from fastapi import APIRouter

from app.routes.catalog.category import router as category_router
from app.routes.catalog.product import router as product_router

catalog_router = APIRouter(prefix="/catalog")
catalog_router.include_router(category_router)
catalog_router.include_router(product_router)

__all__ = ["catalog_router"]
