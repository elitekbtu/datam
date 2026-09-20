import uuid
from collections.abc import Sequence
from decimal import Decimal
from typing import Any, Final

from sqlalchemy import and_, exists, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Product, ProductImage, ProductVariant
from app.schemas.base import Page
from app.schemas.catalog import ProductCreate, ProductRead, ProductUpdate
from app.services.base import DEFAULT_PAGE_SIZE, CRUDService
from app.services.catalog.category import categories
from app.services.catalog.errors import SkuAlreadyExists, SlugAlreadyExists
from app.services.catalog.variant import variants
from app.services.errors import Conflict
from utils.enums import ProductSort

SORT_ORDERS: Final = {
    ProductSort.NEWEST: (Product.created_at.desc(), Product.id),
    ProductSort.OLDEST: (Product.created_at.asc(), Product.id),
    ProductSort.NAME: (Product.name.asc(), Product.id),
    ProductSort.NAME_DESC: (Product.name.desc(), Product.id),
    ProductSort.PRICE: (Product.price.asc(), Product.id),
    ProductSort.PRICE_DESC: (Product.price.desc(), Product.id),
}


class ProductService(CRUDService[Product, ProductRead, ProductCreate, ProductUpdate]):
    """Storage for catalog items and the gallery invariants they carry."""

    model = Product
    read_schema = ProductRead
    nullable_fields = frozenset({"description"})
    unique_fields = ("slug", "sku")
    slug_field = "slug"
    order_by = SORT_ORDERS[ProductSort.NEWEST]
    reload_after_save = True
    not_found_message = "Product not found"

    def conflict(self, field: str) -> Conflict:
        if field == "sku":
            return SkuAlreadyExists("A product with this SKU already exists")
        return SlugAlreadyExists("A product with this slug already exists")

    def arrange(self, images: Sequence[ProductImage]) -> list[ProductImage]:
        """Renumber every gallery from zero, each with exactly one primary photo.

        The product's own photos and each variant's are numbered separately, so
        a variant always keeps a main photo of its own.
        """
        ordered = [
            image
            for _, image in sorted(
                enumerate(images), key=lambda pair: (pair[1].position or 0, pair[0])
            )
        ]
        galleries: dict[uuid.UUID | None, list[ProductImage]] = {}
        for image in ordered:
            galleries.setdefault(image.variant_id, []).append(image)

        for gallery in galleries.values():
            primary = next(
                (image for image in gallery if image.is_primary), gallery[0]
            )
            for position, image in enumerate(gallery):
                image.position = position
                image.is_primary = image is primary
        return ordered

    async def prepare(
        self,
        db: AsyncSession,
        changes: dict[str, Any],
        instance: Product | None = None,
    ) -> dict[str, Any]:
        if (name := changes.get("name")) is not None:
            changes["name"] = name.strip()
        if (sku := changes.get("sku")) is not None:
            changes["sku"] = sku.strip().upper()
        if (category_id := changes.get("category_id")) is not None:
            await categories.require(db, category_id)
        if payloads := changes.pop("variants", None):
            changes["variants"] = await variants.build(db, payloads)
        if images := changes.pop("images", None):
            changes["gallery"] = self.arrange(
                [ProductImage(**image) for image in images]
            )
        return await super().prepare(db, changes, instance)

    def variant_matches(self, *conditions: Any) -> Any:
        """EXISTS over the product's variants, optionally narrowed further."""
        return exists().where(
            ProductVariant.product_id == Product.id,
            ProductVariant.is_active.is_(True),
            *conditions,
        )

    async def search(
        self,
        db: AsyncSession,
        *,
        term: str | None = None,
        category_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        in_stock: bool | None = None,
        sort: ProductSort = ProductSort.NEWEST,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> Page[ProductRead]:
        conditions = []
        if term and (needle := f"%{term.strip().lower()}%"):
            conditions.append(
                or_(
                    func.lower(Product.name).like(needle),
                    func.lower(Product.sku).like(needle),
                    func.lower(Product.description).like(needle),
                    self.variant_matches(
                        or_(
                            func.lower(ProductVariant.sku).like(needle),
                            func.lower(ProductVariant.name).like(needle),
                        )
                    ),
                )
            )
        if category_id is not None:
            conditions.append(Product.category_id == category_id)
        if is_active is not None:
            conditions.append(Product.is_active.is_(is_active))
        if min_price is not None:
            conditions.append(Product.price >= min_price)
        if max_price is not None:
            conditions.append(Product.price <= max_price)
        if in_stock is not None:
            available = or_(
                and_(~self.variant_matches(), Product.stock > 0),
                self.variant_matches(ProductVariant.stock > 0),
            )
            conditions.append(available if in_stock else ~available)
        return await self.paginate(
            db,
            *conditions,
            limit=limit,
            offset=offset,
            order_by=SORT_ORDERS[sort],
        )


products = ProductService()
