from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Category, Product
from app.schemas.base import Page
from app.schemas.catalog import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.base import DEFAULT_PAGE_SIZE, CRUDService
from app.services.catalog.errors import CategoryInUse, SlugAlreadyExists
from app.services.errors import Conflict, InvalidRequest


class CategoryService(
    CRUDService[Category, CategoryRead, CategoryCreate, CategoryUpdate]
):
    """Storage for the sections products are filed under."""

    model = Category
    read_schema = CategoryRead
    nullable_fields = frozenset({"description", "parent_id"})
    unique_fields = ("slug",)
    slug_field = "slug"
    order_by = (Category.name, Category.id)
    not_found_message = "Category not found"

    def conflict(self, field: str) -> Conflict:
        return SlugAlreadyExists("A category with this slug already exists")

    async def prepare(self, db, changes, instance=None):
        parent_id = changes.get("parent_id")
        if parent_id is not None:
            parent = await self.require(db, parent_id)
            seen = {instance.id} if instance is not None else set()
            while parent is not None:
                if parent.id in seen:
                    raise InvalidRequest("Category hierarchy cannot contain a cycle")
                seen.add(parent.id)
                parent = await self.get(db, parent.parent_id) if parent.parent_id else None
        return await super().prepare(db, changes, instance)

    async def descendant_ids(self, db: AsyncSession, category_id) -> list:
        rows = (await db.execute(select(Category.id, Category.parent_id))).all()
        result = {category_id}
        changed = True
        while changed:
            before = len(result)
            result.update(row.id for row in rows if row.parent_id in result)
            changed = len(result) != before
        return list(result)

    async def delete(self, db: AsyncSession, instance: Category) -> None:
        stmt = select(func.count()).select_from(Product).where(
            Product.category_id == instance.id
        )
        if await db.scalar(stmt):
            raise CategoryInUse("Move the products out of this category first")
        if await db.scalar(select(func.count()).select_from(Category).where(Category.parent_id == instance.id)):
            raise CategoryInUse("Move child categories first")
        await super().delete(db, instance)

    async def search(
        self,
        db: AsyncSession,
        *,
        term: str | None = None,
        is_active: bool | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> Page[CategoryRead]:
        conditions = []
        if term and (needle := f"%{term.strip().lower()}%"):
            conditions.append(
                or_(
                    func.lower(Category.name).like(needle),
                    func.lower(Category.slug).like(needle),
                    func.lower(Category.description).like(needle),
                )
            )
        if is_active is not None:
            conditions.append(Category.is_active.is_(is_active))
        return await self.paginate(db, *conditions, limit=limit, offset=offset)


categories = CategoryService()
