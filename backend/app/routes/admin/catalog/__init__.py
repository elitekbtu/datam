from fastapi import APIRouter

from app.routes.admin.catalog.category import router as category_router
from app.routes.admin.catalog.image import router as image_router
from app.routes.admin.catalog.product import router as product_router
from app.routes.admin.catalog.variant import router as variant_router

catalog_router = APIRouter(prefix="/catalog")
catalog_router.include_router(category_router)
catalog_router.include_router(product_router)
catalog_router.include_router(variant_router)
catalog_router.include_router(image_router)

__all__ = ["catalog_router"]
