import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Query

from app.models.catalog import Product
from app.schemas.catalog import ProductPage, ProductRead
from app.services.catalog import categories, products
from core.dependencies import DbSession, PageParams
from utils.enums import ProductSort

router = APIRouter(prefix="/products", tags=["Catalog · Products"])

SearchTerm = Annotated[
    str | None,
    Query(max_length=128, description="Matches name, description, or any SKU"),
]
CategoryKey = Annotated[
    str | None, Query(description="Category id or slug to filter by")
]
PriceBound = Annotated[Decimal | None, Query(ge=0)]


@router.get("", response_model=ProductPage, summary="Browse the catalog")
async def list_products(
    db: DbSession,
    page: PageParams,
    search: SearchTerm = None,
    category: CategoryKey = None,
    min_price: PriceBound = None,
    max_price: PriceBound = None,
    in_stock: bool | None = None,
    sort: ProductSort = ProductSort.NEWEST,
) -> ProductPage:
    category_id: uuid.UUID | None = None
    if category:
        category_id = (await categories.by_key(db, category, active_only=True)).id

    return await products.search(
        db,
        term=search,
        category_id=category_id,
        is_active=True,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        sort=sort,
        limit=page.limit,
        offset=page.offset,
    )


@router.get(
    "/{key}", response_model=ProductRead, summary="Read a product by id or slug"
)
async def read_product(key: str, db: DbSession) -> Product:
    return await products.by_key(db, key, active_only=True)
