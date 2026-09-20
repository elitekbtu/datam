from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Category, Product
from app.schemas.base import Page
from app.schemas.catalog import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.base import DEFAULT_PAGE_SIZE, CRUDService
from app.services.catalog.errors import CategoryInUse, SlugAlreadyExists
from app.services.errors import Conflict


class CategoryService(
    CRUDService[Category, CategoryRead, CategoryCreate, CategoryUpdate]
):
    """Storage for the sections products are filed under."""

    model = Category
    read_schema = CategoryRead
    nullable_fields = frozenset({"description"})
    unique_fields = ("slug",)
    slug_field = "slug"
    order_by = (Category.name, Category.id)
    not_found_message = "Category not found"

    def conflict(self, field: str) -> Conflict:
        return SlugAlreadyExists("A category with this slug already exists")

    async def delete(self, db: AsyncSession, instance: Category) -> None:
        stmt = select(func.count()).select_from(Product).where(
            Product.category_id == instance.id
        )
        if await db.scalar(stmt):
            raise CategoryInUse("Move the products out of this category first")
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
