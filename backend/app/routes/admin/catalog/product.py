import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.models.catalog import Product, ProductVariant
from app.schemas.catalog import (
    ImageOrder,
    ProductCreate,
    ProductImageCreate,
    ProductPage,
    ProductRead,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantRead,
    ProductVariantUpdate,
)
from app.services.catalog import gallery, products, variant, variants
from core.dependencies import DbSession, PageParams, require_admin
from utils.enums import ProductSort

router = APIRouter(
    prefix="/products",
    tags=["Admin · Catalog"],
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
    product_id: uuid.UUID, payload: ProductUpdate, db: DbSession
) -> Product:
    return await products.update(db, await products.require(db, product_id), payload)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product with its variants and photos",
)
async def delete_product(product_id: uuid.UUID, db: DbSession) -> None:
    await products.delete(db, await products.require(db, product_id))


@router.post(
    "/{product_id}/variants",
    response_model=ProductVariantRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a variant, such as one more size",
)
async def add_variant(
    product_id: uuid.UUID, payload: ProductVariantCreate, db: DbSession
) -> ProductVariant:
    product = await products.require(db, product_id)
    return await variants.add_to(db, product, payload)


@router.patch(
    "/{product_id}/variants/{variant_id}",
    response_model=ProductVariantRead,
    summary="Update a variant",
)
async def update_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    payload: ProductVariantUpdate,
    db: DbSession,
) -> ProductVariant:
    product = await products.require(db, product_id)
    return await variants.update(db, variant.find(product, variant_id), payload)


@router.delete(
    "/{product_id}/variants/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a variant with its photos",
)
async def delete_variant(
    product_id: uuid.UUID, variant_id: uuid.UUID, db: DbSession
) -> None:
    product = await products.require(db, product_id)
    await variants.delete(db, variant.find(product, variant_id))


@router.post(
    "/{product_id}/images",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a photo to the product or to one of its variants",
)
async def add_image(
    product_id: uuid.UUID, payload: ProductImageCreate, db: DbSession
) -> Product:
    return await gallery.add(db, await products.require(db, product_id), payload)


@router.delete(
    "/{product_id}/images/{image_id}",
    response_model=ProductRead,
    summary="Remove a photo",
)
async def remove_image(
    product_id: uuid.UUID, image_id: uuid.UUID, db: DbSession
) -> Product:
    return await gallery.remove(db, await products.require(db, product_id), image_id)


@router.put(
    "/{product_id}/images/order",
    response_model=ProductRead,
    summary="Reorder one gallery",
)
async def reorder_images(
    product_id: uuid.UUID, payload: ImageOrder, db: DbSession
) -> Product:
    product = await products.require(db, product_id)
    return await gallery.reorder(db, product, payload.image_ids)


@router.put(
    "/{product_id}/images/{image_id}/primary",
    response_model=ProductRead,
    summary="Make a photo the main one of its gallery",
)
async def set_primary_image(
    product_id: uuid.UUID, image_id: uuid.UUID, db: DbSession
) -> Product:
    product = await products.require(db, product_id)
    return await gallery.set_primary(db, product, image_id)
