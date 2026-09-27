"""Idempotent demo fashion catalog. Run after Alembic migrations."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.models.catalog import Category, Product, ProductImage, ProductVariant
from database.session import AsyncSessionLocal
from utils.enums import Audience, Currency

CATEGORIES = [
    ("clothing", "Одежда", None),
    ("shoes", "Обувь", None),
    ("accessories", "Аксессуары", None),
    ("blazers", "Пиджаки", "clothing"),
    ("dresses", "Платья", "clothing"),
    ("trousers", "Брюки", "clothing"),
    ("knitwear", "Трикотаж", "clothing"),
    ("outerwear", "Верхняя одежда", "clothing"),
    ("sneakers", "Кроссовки", "shoes"),
    ("boots", "Ботинки", "shoes"),
    ("bags", "Сумки", "accessories"),
]

PRODUCTS = [
    {
        "slug": "black-wool-blazer",
        "name": "Пиджак из шерсти",
        "sku": "DT-BL-001",
        "price": "89900",
        "description": "Структурный пиджак из плотной шерстяной ткани. Чистая линия плеч и лаконичный силуэт для повседневных образов.",
        "category": "blazers",
        "audience": Audience.WOMEN,
        "images": ["blazer", "blazer-back", "blazer-detail", "blazer-side"],
        "sizes": ["S", "M", "L"],
    },
    {
        "slug": "ivory-ribbed-knit",
        "name": "Джемпер с высоким воротом",
        "sku": "DT-KN-002",
        "price": "49900",
        "description": "Мягкий объёмный трикотаж молочного оттенка с выразительной фактурой.",
        "category": "knitwear",
        "audience": Audience.WOMEN,
        "images": ["knit"],
        "sizes": ["S", "M", "L"],
    },
    {
        "slug": "black-wool-coat",
        "name": "Пальто из шерсти",
        "sku": "DT-CT-003",
        "price": "129900",
        "description": "Длинное шерстяное пальто с прямым силуэтом и сдержанными деталями.",
        "category": "outerwear",
        "audience": Audience.MEN,
        "images": ["coat"],
        "sizes": ["M", "L", "XL"],
    },
    {
        "slug": "black-merino-turtleneck",
        "name": "Свитер из мериносовой шерсти",
        "sku": "DT-TN-004",
        "price": "59900",
        "description": "Тонкий тёплый трикотаж с высоким воротом для многослойных образов.",
        "category": "knitwear",
        "audience": Audience.MEN,
        "images": ["turtleneck"],
        "sizes": ["M", "L", "XL"],
    },
    {
        "slug": "ivory-leather-sneakers",
        "name": "Кожаные кроссовки",
        "sku": "DT-SH-005",
        "price": "69900",
        "description": "Минималистичные кроссовки из светлой кожи и мягкой замши.",
        "category": "sneakers",
        "audience": Audience.UNISEX,
        "images": ["sneakers"],
        "sizes": ["38", "39", "40", "41", "42", "43"],
    },
    {
        "slug": "structured-leather-bag",
        "name": "Сумка из натуральной кожи",
        "sku": "DT-BG-006",
        "price": "99900",
        "description": "Структурная сумка из чёрной кожи с лаконичной фурнитурой.",
        "category": "bags",
        "audience": Audience.WOMEN,
        "images": ["bag"],
        "sizes": [],
    },
    {
        "slug": "ivory-tailored-blazer",
        "name": "Пиджак прямого кроя",
        "sku": "DT-BL-007",
        "price": "84900",
        "description": "Лёгкий пиджак молочного оттенка с мягкой линией плеч и точной посадкой.",
        "category": "blazers",
        "audience": Audience.WOMEN,
        "images": ["ivory-blazer"],
        "sizes": ["S", "M", "L"],
    },
    {
        "slug": "black-midi-dress",
        "name": "Платье миди",
        "sku": "DT-DR-008",
        "price": "64900",
        "description": "Лаконичное чёрное платье миди для спокойных вечерних образов.",
        "category": "dresses",
        "audience": Audience.WOMEN,
        "images": ["dress"],
        "sizes": ["S", "M", "L"],
    },
    {
        "slug": "charcoal-tailored-trousers",
        "name": "Брюки со стрелками",
        "sku": "DT-TR-009",
        "price": "54900",
        "description": "Прямые брюки угольного оттенка из плотной костюмной ткани.",
        "category": "trousers",
        "audience": Audience.MEN,
        "images": ["trousers"],
        "sizes": ["M", "L", "XL"],
    },
    {
        "slug": "black-leather-ankle-boots",
        "name": "Кожаные ботинки",
        "sku": "DT-SH-010",
        "price": "78900",
        "description": "Чёрные кожаные ботинки с чистым силуэтом и устойчивой подошвой.",
        "category": "boots",
        "audience": Audience.WOMEN,
        "images": ["boots"],
        "sizes": ["37", "38", "39", "40", "41"],
    },
]


async def main() -> None:
    async with AsyncSessionLocal() as db:
        category_ids = {}
        for slug, name, parent_slug in CATEGORIES:
            category = await db.scalar(select(Category).where(Category.slug == slug))
            if category is None:
                category = Category(
                    id=uuid.uuid4(),
                    slug=slug,
                    name=name,
                    parent_id=category_ids.get(parent_slug),
                    is_active=True,
                )
                db.add(category)
                await db.flush()
            category_ids[slug] = category.id
        for index, item in enumerate(PRODUCTS):
            if await db.scalar(select(Product.id).where(Product.slug == item["slug"])):
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
                audience=item["audience"],
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
