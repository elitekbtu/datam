from fastapi import APIRouter
from app.routes.commerce.cart import router as cart_router
from app.routes.commerce.favorites import router as favorites_router
from app.routes.commerce.orders import router as orders_router

commerce_router = APIRouter()
commerce_router.include_router(cart_router)
commerce_router.include_router(favorites_router)
commerce_router.include_router(orders_router)

__all__ = ["commerce_router"]
