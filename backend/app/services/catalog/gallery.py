"""Photos of a product and of its variants: added, removed, reordered, promoted."""

import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Product, ProductImage
from app.schemas.catalog import ProductImageCreate
from app.services.catalog.errors import ImageNotFound, InvalidImageOrder
from app.services.catalog import storage
from app.services.catalog.product import products
from app.services.catalog.variant import find as find_variant


def find(product: Product, image_id: uuid.UUID) -> ProductImage:
    for image in product.gallery:
        if image.id == image_id:
            return image
    raise ImageNotFound("This product has no such photo")


def group_of(product: Product, variant_id: uuid.UUID | None) -> list[ProductImage]:
    """The photos of one variant, or the product's own when ``variant_id`` is None."""
    return [image for image in product.gallery if image.variant_id == variant_id]


async def save(db: AsyncSession, product: Product) -> Product:
    product.gallery = products.arrange(product.gallery)
    return await products.save(db, product)


async def add(
    db: AsyncSession, product: Product, payload: ProductImageCreate
) -> Product:
    changes = payload.model_dump()
    if changes["variant_id"] is not None:
        find_variant(product, changes["variant_id"])
    if changes["position"] is None:
        changes["position"] = len(group_of(product, changes["variant_id"]))
    product.gallery.append(ProductImage(**changes))
    return await save(db, product)


async def upload(
    db: AsyncSession,
    product: Product,
    file: UploadFile,
    *,
    variant_id: uuid.UUID | None = None,
    alt_text: str | None = None,
    is_primary: bool = False,
) -> Product:
    """Store an uploaded file next to the product and hang it in the gallery."""
    if variant_id is not None:
        find_variant(product, variant_id)
    url = await storage.save(file, f"products/{product.id}")
    return await add(
        db,
        product,
        ProductImageCreate(
            url=url, variant_id=variant_id, alt_text=alt_text, is_primary=is_primary
        ),
    )


async def remove(db: AsyncSession, product: Product, image_id: uuid.UUID) -> Product:
    image = find(product, image_id)
    url = image.url
    product.gallery.remove(image)
    product = await save(db, product)
    storage.discard([url])
    return product


async def reorder(
    db: AsyncSession, product: Product, image_ids: list[uuid.UUID]
) -> Product:
    if len(set(image_ids)) != len(image_ids):
        raise InvalidImageOrder("List every photo of this gallery exactly once")

    images = [find(product, image_id) for image_id in image_ids]
    galleries = {image.variant_id for image in images}
    if len(galleries) != 1:
        raise InvalidImageOrder("Reorder the photos of one gallery at a time")

    gallery = group_of(product, galleries.pop())
    if {image.id for image in images} != {image.id for image in gallery}:
        raise InvalidImageOrder("List every photo of this gallery exactly once")

    for position, image in enumerate(images):
        image.position = position
    return await save(db, product)


async def set_primary(
    db: AsyncSession, product: Product, image_id: uuid.UUID
) -> Product:
    target = find(product, image_id)
    for image in group_of(product, target.variant_id):
        image.is_primary = image.id == image_id
    return await save(db, product)
