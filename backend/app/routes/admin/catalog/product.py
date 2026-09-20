import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.models.catalog import Product
from app.routes.admin.catalog.dependencies import TargetProduct
from app.schemas.catalog import ProductCreate, ProductPage, ProductRead, ProductUpdate
from app.services.catalog import products
from core.dependencies import DbSession, PageParams, require_admin
from utils.enums import ProductSort

router = APIRouter(
    prefix="/products",
    tags=["Admin · Products"],
    dependencies=[Depends(require_admin)],
)

SearchTerm = Annotated[
    str | None,
    Query(max_length=128, description="Matches name, description, or any SKU"),
]
PriceBound = Annotated[Decimal | None, Query(ge=0)]


@router.get("", response_model=ProductPage, summary="List and filter products")
async def list_products(
    db: DbSession,
    page: PageParams,
    search: SearchTerm = None,
    category_id: uuid.UUID | None = None,
    is_active: bool | None = None,
    min_price: PriceBound = None,
    max_price: PriceBound = None,
    in_stock: bool | None = None,
    sort: ProductSort = ProductSort.NEWEST,
) -> ProductPage:
    return await products.search(
        db,
        term=search,
        category_id=category_id,
        is_active=is_active,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        sort=sort,
        limit=page.limit,
        offset=page.offset,
    )


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product, with its variants and photos",
)
async def create_product(payload: ProductCreate, db: DbSession) -> Product:
    return await products.create(db, payload)


@router.get("/{key}", response_model=ProductRead, summary="Read a product")
async def read_product(key: str, db: DbSession) -> Product:
    return await products.by_key(db, key)


@router.patch("/{product_id}", response_model=ProductRead, summary="Update a product")
async def update_product(
    product: TargetProduct, payload: ProductUpdate, db: DbSession
) -> Product:
    return await products.update(db, product, payload)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product with its variants and photos",
)
async def delete_product(product: TargetProduct, db: DbSession) -> None:
    await products.delete(db, product)
