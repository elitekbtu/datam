from collections.abc import Sequence
from typing import Any, Final

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.base import Page, ReadSchema, WriteSchema
from app.services.errors import NotFound
from database.base import Base

DEFAULT_PAGE_SIZE: Final = 50
MAX_PAGE_SIZE: Final = 100


class CRUDService[
    ModelT: Base,
    ReadT: ReadSchema,
    CreateT: WriteSchema,
    UpdateT: WriteSchema,
]:
    """Create, read, update, and delete shared by every entity service."""

    model: type[ModelT]
    read_schema: type[ReadT]
    nullable_fields: frozenset[str] = frozenset()
    order_by: Sequence[Any] = ()
    not_found_message: str = "Resource not found"

    def collect(self, payload: WriteSchema, *, partial: bool) -> dict[str, Any]:
        """Turn a payload into column assignments, dropping meaningless nulls."""
        data = payload.model_dump(exclude_unset=partial)
        return {
            field: value
            for field, value in data.items()
            if value is not None or field in self.nullable_fields
        }

    async def prepare(
        self,
        db: AsyncSession,
        changes: dict[str, Any],
        instance: ModelT | None = None,
    ) -> dict[str, Any]:
        """Hook run before every write; ``instance`` is None on creation."""
        return changes

    async def save(self, db: AsyncSession, instance: ModelT) -> ModelT:
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
        return instance

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

    async def create(self, db: AsyncSession, payload: CreateT) -> ModelT:
        changes = await self.prepare(db, self.collect(payload, partial=False))
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
    ) -> Page[ReadT]:
        total = await db.scalar(
            select(func.count()).select_from(self.model).where(*conditions)
        )
        stmt = (
            select(self.model)
            .where(*conditions)
            .order_by(*self.order_by)
            .limit(limit)
            .offset(offset)
        )
        instances = await db.scalars(stmt)
        return Page[self.read_schema](
            items=[self.read_schema.model_validate(row) for row in instances],
            total=total or 0,
            limit=limit,
            offset=offset,
        )
