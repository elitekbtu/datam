from typing import Annotated

from fastapi import APIRouter, Query

from app.models.catalog import Category
from app.schemas.catalog import CategoryPage, CategoryRead
from app.services.catalog import categories
from core.dependencies import DbSession, PageParams

router = APIRouter(prefix="/categories", tags=["Catalog"])

SearchTerm = Annotated[
    str | None, Query(max_length=128, description="Matches name, slug, or description")
]


@router.get("", response_model=CategoryPage, summary="Browse categories")
async def list_categories(
    db: DbSession, page: PageParams, search: SearchTerm = None
) -> CategoryPage:
    return await categories.search(
        db, term=search, is_active=True, limit=page.limit, offset=page.offset
    )


@router.get(
    "/{key}", response_model=CategoryRead, summary="Read a category by id or slug"
)
async def read_category(key: str, db: DbSession) -> Category:
    return await categories.by_key(db, key, active_only=True)
