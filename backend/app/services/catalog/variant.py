"""The buyable flavours of one product: sizes, colours, anything with its own SKU."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Product, ProductVariant
from app.schemas.catalog import (
    ProductVariantCreate,
    ProductVariantRead,
    ProductVariantUpdate,
)
from app.services.base import CRUDService
from app.services.catalog.errors import SkuAlreadyExists, VariantNotFound
from app.services.errors import Conflict


class VariantService(
    CRUDService[
        ProductVariant,
        ProductVariantRead,
        ProductVariantCreate,
        ProductVariantUpdate,
    ]
):
    model = ProductVariant
    read_schema = ProductVariantRead
    nullable_fields = frozenset({"price"})
    unique_fields = ("sku",)
    order_by = (ProductVariant.position, ProductVariant.id)
    reload_after_save = True
    not_found_message = "Variant not found"

    def conflict(self, field: str) -> Conflict:
        return SkuAlreadyExists("A variant with this SKU already exists")

    async def prepare(
        self,
        db: AsyncSession,
        changes: dict[str, Any],
        instance: ProductVariant | None = None,
    ) -> dict[str, Any]:
        if (name := changes.get("name")) is not None:
            changes["name"] = name.strip()
        if (sku := changes.get("sku")) is not None:
            changes["sku"] = sku.strip().upper()
        return await super().prepare(db, changes, instance)

    async def add_to(
        self, db: AsyncSession, product: Product, payload: ProductVariantCreate
    ) -> ProductVariant:
        position = payload.position
        return await self.create(
            db,
            payload,
            product_id=product.id,
            position=len(product.variants) if position is None else position,
        )

    async def build(
        self, db: AsyncSession, payloads: list[dict[str, Any]]
    ) -> list[ProductVariant]:
        """Rows for the variants sent alongside a brand new product."""
        built: list[ProductVariant] = []
        taken: set[str] = set()
        for position, payload in enumerate(payloads):
            changes = await self.prepare(db, dict(payload))
            if changes["sku"] in taken:
                raise SkuAlreadyExists(f"SKU {changes['sku']} is listed twice")
            taken.add(changes["sku"])
            if changes.get("position") is None:
                changes["position"] = position
            built.append(ProductVariant(**changes))
        return built


def find(product: Product, variant_id: uuid.UUID) -> ProductVariant:
    for variant in product.variants:
        if variant.id == variant_id:
            return variant
    raise VariantNotFound("This product has no such variant")


variants = VariantService()
