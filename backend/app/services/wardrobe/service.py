import uuid

from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wardrobe import WardrobeItem
from app.schemas.base import Page
from app.schemas.wardrobe import WardrobeItemCreate, WardrobeItemRead, WardrobeItemUpdate
from app.services.base import DEFAULT_PAGE_SIZE, CRUDService
from app.services.catalog import categories, storage
from app.services.commerce.common import get_product, image_for
from app.services.wardrobe.errors import UnknownCategory, WardrobeItemNotFound
from core.config import settings
from utils.enums import Formality

FOLDER = "wardrobe"


def folder_of(user_id: uuid.UUID) -> str:
    return f"{FOLDER}/{user_id}"


def is_own_photo(url: str | None) -> bool:
    """Photos copied from a product stay with the catalog; only uploads are ours."""
    return bool(url) and url.startswith(f"{settings.MEDIA_URL.rstrip('/')}/{FOLDER}/")


def discard_own_photo(url: str | None) -> None:
    if is_own_photo(url):
        storage.discard([url])


def like_pattern(term: str) -> str:
    escaped = term.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


class WardrobeService(
    CRUDService[WardrobeItem, WardrobeItemRead, WardrobeItemCreate, WardrobeItemUpdate]
):
    """Clothes a user owns; every lookup is scoped to that user."""

    model = WardrobeItem
    read_schema = WardrobeItemRead
    nullable_fields = frozenset({"category_id", "formality", "color", "note"})
    order_by = (WardrobeItem.created_at.desc(), WardrobeItem.id)
    not_found_message = "Wardrobe item not found"

    async def prepare(self, db, changes, instance=None):
        category_id = changes.get("category_id")
        unchanged = instance is not None and category_id == instance.category_id
        if category_id is not None and not unchanged:
            category = await categories.get(db, category_id)
            if category is None or not category.is_active:
                raise UnknownCategory("Choose an existing category")
        return await super().prepare(db, changes, instance)

    async def owned(self, db: AsyncSession, user_id: uuid.UUID, item_id: uuid.UUID) -> WardrobeItem:
        item = await self.get(db, item_id)
        if item is None or item.user_id != user_id:
            raise WardrobeItemNotFound(self.not_found_message)
        return item

    async def search(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        *,
        term: str | None = None,
        category_id: uuid.UUID | None = None,
        formality: Formality | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> Page[WardrobeItemRead]:
        conditions = [WardrobeItem.user_id == user_id]
        if term and (term := term.strip()):
            needle = like_pattern(term)
            conditions.append(
                or_(
                    *(
                        func.lower(column).like(needle, escape="\\")
                        for column in (WardrobeItem.name, WardrobeItem.color, WardrobeItem.note)
                    )
                )
            )
        if category_id is not None:
            conditions.append(WardrobeItem.category_id == category_id)
        if formality is not None:
            conditions.append(WardrobeItem.formality == formality)
        return await self.paginate(db, *conditions, limit=limit, offset=offset)

    async def from_product(
        self, db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID
    ) -> WardrobeItem:
        """Add a catalog product to the wardrobe once, copying what describes it."""
        product = await get_product(db, product_id)
        existing = await db.scalar(
            select(WardrobeItem).where(
                WardrobeItem.user_id == user_id, WardrobeItem.product_id == product.id
            )
        )
        if existing is not None:
            return existing
        item = WardrobeItem(
            user_id=user_id,
            product_id=product.id,
            name=product.name,
            category_id=product.category_id,
            formality=product.formality,
            color=product.color,
            image_url=image_for(product, None),
        )
        return await self.save(db, item)

    async def set_photo(
        self, db: AsyncSession, item: WardrobeItem, file: UploadFile
    ) -> WardrobeItem:
        previous = item.image_url
        item.image_url = await storage.save(file, folder_of(item.user_id))
        try:
            item = await self.save(db, item)
        except Exception:
            discard_own_photo(item.image_url)
            raise
        discard_own_photo(previous)
        return item

    async def remove_photo(self, db: AsyncSession, item: WardrobeItem) -> WardrobeItem:
        previous, item.image_url = item.image_url, None
        item = await self.save(db, item)
        discard_own_photo(previous)
        return item

    async def delete(self, db: AsyncSession, instance: WardrobeItem) -> None:
        photo = instance.image_url
        await super().delete(db, instance)
        discard_own_photo(photo)


wardrobe = WardrobeService()
