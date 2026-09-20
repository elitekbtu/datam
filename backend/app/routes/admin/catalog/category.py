import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.models.catalog import Category
from app.schemas.catalog import (
    CategoryCreate,
    CategoryPage,
    CategoryRead,
    CategoryUpdate,
)
from app.services.catalog import categories
from core.dependencies import DbSession, PageParams, require_admin

router = APIRouter(
    prefix="/categories",
    tags=["Admin · Catalog"],
    dependencies=[Depends(require_admin)],
)

SearchTerm = Annotated[
    str | None, Query(max_length=128, description="Matches name, slug, or description")
]


@router.get("", response_model=CategoryPage, summary="List and filter categories")
async def list_categories(
    db: DbSession,
    page: PageParams,
    search: SearchTerm = None,
    is_active: bool | None = None,
) -> CategoryPage:
    return await categories.search(
        db, term=search, is_active=is_active, limit=page.limit, offset=page.offset
    )


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category",
)
async def create_category(payload: CategoryCreate, db: DbSession) -> Category:
    return await categories.create(db, payload)


@router.get("/{key}", response_model=CategoryRead, summary="Read a category")
async def read_category(key: str, db: DbSession) -> Category:
    return await categories.by_key(db, key)


@router.patch(
    "/{category_id}", response_model=CategoryRead, summary="Update a category"
)
async def update_category(
    category_id: uuid.UUID, payload: CategoryUpdate, db: DbSession
) -> Category:
    category = await categories.require(db, category_id)
    return await categories.update(db, category, payload)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an empty category",
)
async def delete_category(category_id: uuid.UUID, db: DbSession) -> None:
    await categories.delete(db, await categories.require(db, category_id))
