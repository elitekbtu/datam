"""What the store can sell right now, as the stylist sees it."""

import uuid
from decimal import Decimal
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Category, Product, ProductVariant
from app.services.commerce.common import price_for
from utils.enums import Audience, Currency


class Offer(NamedTuple):
    """A product the store can sell right now, in its suggested size."""

    product: Product
    variant: ProductVariant | None
    price: Decimal


def suggested_variant(product: Product) -> ProductVariant | None:
    """The first in-stock size, or ``None`` for a product sold without sizes."""
    return next(
        (v for v in product.variants if v.is_active and v.stock > 0), None
    )


async def sellable(db: AsyncSession, audience: Audience | None) -> list[Offer]:
    """Every product a shopper could order right now, newest first."""
    query = (
        select(Product)
        .join(Category, Product.category_id == Category.id)
        .where(
            Product.is_active.is_(True),
            Category.is_active.is_(True),
            Product.currency == Currency.KZT,
        )
        .order_by(Product.created_at.desc(), Product.id)
    )
    if audience is not None:
        query = query.where(Product.audience.in_([audience, Audience.UNISEX]))

    offers = []
    for product in (await db.scalars(query)).unique():
        if product.in_stock:
            variant = suggested_variant(product)
            offers.append(Offer(product, variant, price_for(product, variant)))
    return offers


async def active_categories(db: AsyncSession) -> list[Category]:
    return list(await db.scalars(select(Category).where(Category.is_active.is_(True))))


def descendants(root: uuid.UUID, categories: list[Category]) -> frozenset[uuid.UUID]:
    """The category and everything nested under it: «Обувь» → shoes of all kinds."""
    found, frontier = {root}, [root]
    while frontier:
        parent = frontier.pop()
        for category in categories:
            if category.parent_id == parent and category.id not in found:
                found.add(category.id)
                frontier.append(category.id)
    return frozenset(found)
