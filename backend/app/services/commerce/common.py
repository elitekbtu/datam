import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.catalog import Product, ProductVariant
from app.services.errors import InvalidRequest, NotFound


async def get_product(db: AsyncSession, product_id: uuid.UUID) -> Product:
    product = (
        (await db.scalars(select(Product).where(Product.id == product_id)))
        .unique()
        .one_or_none()
    )
    if product is None or not product.is_active or not product.category.is_active:
        raise NotFound("Product not found")
    return product


def variant_for(
    product: Product, variant_id: uuid.UUID | None
) -> ProductVariant | None:
    if product.variants:
        variant = next(
            (v for v in product.variants if v.id == variant_id and v.is_active), None
        )
        if variant is None:
            raise InvalidRequest("Choose an available size or variant")
        return variant
    if variant_id is not None:
        raise InvalidRequest("This product has no variants")
    return None


def image_for(product: Product, variant: ProductVariant | None) -> str | None:
    images = variant.images if variant and variant.images else product.images
    main = next((image for image in images if image.is_primary), None)
    return (main or (images[0] if images else None)).url if images else None


def price_for(product: Product, variant: ProductVariant | None) -> Decimal:
    return variant.price if variant and variant.price is not None else product.price
