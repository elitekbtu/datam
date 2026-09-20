import uuid

from fastapi import APIRouter, Depends, status

from app.models.catalog import ProductVariant
from app.routes.admin.catalog.dependencies import TargetProduct
from app.schemas.catalog import (
    ProductVariantCreate,
    ProductVariantRead,
    ProductVariantUpdate,
)
from app.services.catalog import variant, variants
from core.dependencies import DbSession, require_admin

router = APIRouter(
    prefix="/products/{product_id}/variants",
    tags=["Admin · Variants"],
    dependencies=[Depends(require_admin)],
)


@router.post(
    "",
    response_model=ProductVariantRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a variant, such as one more size",
)
async def add_variant(
    product: TargetProduct, payload: ProductVariantCreate, db: DbSession
) -> ProductVariant:
    return await variants.add_to(db, product, payload)


@router.patch(
    "/{variant_id}", response_model=ProductVariantRead, summary="Update a variant"
)
async def update_variant(
    product: TargetProduct,
    variant_id: uuid.UUID,
    payload: ProductVariantUpdate,
    db: DbSession,
) -> ProductVariant:
    return await variants.update(db, variant.find(product, variant_id), payload)


@router.delete(
    "/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a variant with its photos",
)
async def delete_variant(
    product: TargetProduct, variant_id: uuid.UUID, db: DbSession
) -> None:
    await variants.delete(db, variant.find(product, variant_id))
