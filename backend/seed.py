"""Idempotent demo catalog from data/catalog.json; existing products get their tags refreshed."""

import asyncio
import json
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app.models.catalog import Category, Product, ProductImage, ProductVariant
from database.session import AsyncSessionLocal
from utils.enums import Audience, Currency, Formality

CATALOG = Path(__file__).parent / "data" / "catalog.json"


def load_catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


async def main() -> None:
    catalog = load_catalog()
    async with AsyncSessionLocal() as db:
        category_ids = {}
        for item in catalog["categories"]:
            category = await db.scalar(select(Category).where(Category.slug == item["slug"]))
            if category is None:
                category = Category(
                    id=uuid.uuid4(),
                    slug=item["slug"],
                    name=item["name"],
                    parent_id=category_ids.get(item["parent"]),
                    is_active=True,
                )
                db.add(category)
                await db.flush()
            category_ids[item["slug"]] = category.id
        for index, item in enumerate(catalog["products"]):
            formality = Formality(item["formality"]) if item.get("formality") else None
            existing = await db.scalar(select(Product).where(Product.slug == item["slug"]))
            if existing is not None:
                existing.formality = formality
                existing.color = item.get("color")
                continue
            product_id = uuid.uuid4()
            product = Product(
                id=product_id,
                slug=item["slug"],
                name=item["name"],
                sku=item["sku"],
                description=item["description"],
                price=Decimal(item["price"]),
                currency=Currency.KZT,
                stock=0 if item["sizes"] else 12,
                category_id=category_ids[item["category"]],
                audience=Audience(item["audience"]),
                formality=formality,
                color=item.get("color"),
                is_active=True,
                created_at=datetime.now(UTC) - timedelta(minutes=index),
            )
            db.add(product)
            for position, name in enumerate(item["images"]):
                db.add(
                    ProductImage(
                        product_id=product_id,
                        url=f"/images/{name}.webp",
                        alt_text=item["name"],
                        position=position,
                        is_primary=position == 0,
                    )
                )
            for position, size in enumerate(item["sizes"]):
                db.add(
                    ProductVariant(
                        product_id=product_id,
                        name=size,
                        sku=f"{item['sku']}-{size}",
                        options={"size": size},
                        stock=8 + position * 2,
                        is_active=True,
                        position=position,
                    )
                )
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
