import uuid
from typing import Annotated

from fastapi import Depends

from app.models.catalog import Product
from app.services.catalog import products
from core.dependencies import DbSession


async def get_product(product_id: uuid.UUID, db: DbSession) -> Product:
    """The product a nested route hangs under, resolved once per request."""
    return await products.require(db, product_id)


TargetProduct = Annotated[Product, Depends(get_product)]
