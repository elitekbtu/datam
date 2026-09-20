import uuid
from collections.abc import Sequence
from typing import Any, Final

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.base import Page, ReadSchema, WriteSchema
from app.services.errors import Conflict, InvalidRequest, NotFound
from database.base import Base
from utils.text import slugify

DEFAULT_PAGE_SIZE: Final = 50
MAX_PAGE_SIZE: Final = 100


class CRUDService[
    ModelT: Base,
    ReadT: ReadSchema,
    CreateT: WriteSchema,
    UpdateT: WriteSchema,
]:
    """Create, read, update, and delete shared by every entity service.

    A subclass binds a model to its schemas and overrides :meth:`prepare` to
    normalise values before they reach the database.
    """

    model: type[ModelT]
    read_schema: type[ReadT]
    #: Columns that accept an explicit ``null``; any other field ignores one.
    nullable_fields: frozenset[str] = frozenset()
    #: Columns whose value no other row may hold, checked case-insensitively.
    unique_fields: Sequence[str] = ()
    #: Column that addresses a row in a URL, and the column it is derived from.
    slug_field: str | None = None
    slug_source: str = "name"
    order_by: Sequence[Any] = ()
    #: Re-read a row after each write, so eager relationships come back loaded.
    reload_after_save: bool = False
    not_found_message: str = "Resource not found"

    def conflict(self, field: str) -> Conflict:
        """Error raised when :attr:`unique_fields` is already taken."""
        return Conflict(f"This {field.replace('_', ' ')} is already taken")

    def collect(self, payload: WriteSchema, *, partial: bool) -> dict[str, Any]:
        """Turn a payload into column assignments, dropping meaningless nulls."""
        data = payload.model_dump(exclude_unset=partial)
        return {
            field: value
            for field, value in data.items()
            if value is not None or field in self.nullable_fields
        }

    def apply_slug(self, changes: dict[str, Any], instance: ModelT | None) -> None:
        """Fill the slug from its source column when the client left it out."""
        if self.slug_field is None:
            return
        source = changes.get(self.slug_field)
        if source is None:
            if instance is not None:
                return
            source = str(changes.get(self.slug_source, ""))
        if not (slug := slugify(source)):
            raise InvalidRequest(
                f"Could not build a {self.slug_field} from {source!r}; send one"
            )
        changes[self.slug_field] = slug

    async def ensure_unique(
        self,
        db: AsyncSession,
        changes: dict[str, Any],
        instance: ModelT | None = None,
    ) -> None:
        wanted = {
            field: changes[field]
            for field in self.unique_fields
            if changes.get(field) is not None
        }
        if not wanted:
            return

        stmt = select(self.model).where(
            or_(*(self.matches(field, value) for field, value in wanted.items()))
        )
        if instance is not None:
            stmt = stmt.where(self.model.id != instance.id)

        taken = await db.scalar(stmt)
        if taken is None:
            return
        for field, value in wanted.items():
            if self.same(getattr(taken, field), value):
                raise self.conflict(field)
        raise self.conflict(next(iter(wanted)))

    def matches(self, field: str, value: Any) -> ColumnElement[bool]:
        column = getattr(self.model, field)
        if isinstance(value, str):
            return func.lower(column) == value.lower()
        return column == value

    @staticmethod
    def same(stored: Any, wanted: Any) -> bool:
        if isinstance(stored, str) and isinstance(wanted, str):
            return stored.lower() == wanted.lower()
        return stored == wanted

    async def prepare(
        self,
        db: AsyncSession,
        changes: dict[str, Any],
        instance: ModelT | None = None,
    ) -> dict[str, Any]:
        """Hook run before every write; ``instance`` is None on creation."""
        self.apply_slug(changes, instance)
        await self.ensure_unique(db, changes, instance)
        return changes

    async def save(self, db: AsyncSession, instance: ModelT) -> ModelT:
        db.add(instance)
        await db.commit()
        if self.reload_after_save:
            return await self.reload(db, instance)
        await db.refresh(instance)
        return instance

    async def reload(self, db: AsyncSession, instance: ModelT) -> ModelT:
        """Read the row back, letting every eager loader repopulate it."""
        stmt = (
            select(self.model)
            .where(self.model.id == instance.id)
            .execution_options(populate_existing=True)
        )
        return (await db.scalars(stmt)).unique().one()

    async def apply(
        self, db: AsyncSession, instance: ModelT, changes: dict[str, Any]
    ) -> ModelT:
        for field, value in changes.items():
            setattr(instance, field, value)
        return await self.save(db, instance)

    async def get(self, db: AsyncSession, obj_id: Any) -> ModelT | None:
        return await db.get(self.model, obj_id)

    async def require(self, db: AsyncSession, obj_id: Any) -> ModelT:
        instance = await self.get(db, obj_id)
        if instance is None:
            raise NotFound(self.not_found_message)
        return instance

    async def by_key(
        self, db: AsyncSession, key: str, *, active_only: bool = False
    ) -> ModelT:
        """Look a row up by id, or by :attr:`slug_field` when the key is a slug."""
        try:
            instance = await self.get(db, uuid.UUID(key))
        except ValueError:
            if self.slug_field is None:
                raise NotFound(self.not_found_message) from None
            column = getattr(self.model, self.slug_field)
            instance = await db.scalar(select(self.model).where(column == key.lower()))

        if instance is None:
            raise NotFound(self.not_found_message)
        if active_only and not getattr(instance, "is_active", True):
            raise NotFound(self.not_found_message)
        return instance

    async def create(
        self, db: AsyncSession, payload: CreateT, **extra: Any
    ) -> ModelT:
        changes = await self.prepare(db, self.collect(payload, partial=False) | extra)
        return await self.save(db, self.model(**changes))

    async def update(
        self, db: AsyncSession, instance: ModelT, payload: UpdateT
    ) -> ModelT:
        changes = self.collect(payload, partial=True)
        return await self.apply(db, instance, await self.prepare(db, changes, instance))

    async def delete(self, db: AsyncSession, instance: ModelT) -> None:
        await db.delete(instance)
        await db.commit()

    async def paginate(
        self,
        db: AsyncSession,
        *conditions: ColumnElement[bool],
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
        order_by: Sequence[Any] | None = None,
    ) -> Page[ReadT]:
        total = await db.scalar(
            select(func.count()).select_from(self.model).where(*conditions)
        )
        stmt = (
            select(self.model)
            .where(*conditions)
            .order_by(*(order_by or self.order_by))
            .limit(limit)
            .offset(offset)
        )
        instances = await db.scalars(stmt)
        return Page[self.read_schema](
            items=[self.read_schema.model_validate(row) for row in instances.unique()],
            total=total or 0,
            limit=limit,
            offset=offset,
        )
