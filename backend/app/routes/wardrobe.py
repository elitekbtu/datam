import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.models.wardrobe import WardrobeItem
from app.schemas.wardrobe import (
    WardrobeItemCreate,
    WardrobeItemFromProduct,
    WardrobeItemPage,
    WardrobeItemRead,
    WardrobeItemUpdate,
)
from app.services.catalog.storage import IMAGE_TYPES
from app.services.wardrobe import wardrobe
from core.dependencies import CurrentUser, DbSession, PageParams
from utils.enums import Formality

router = APIRouter(prefix="/wardrobe", tags=["Wardrobe"])

SearchTerm = Annotated[str | None, Query(max_length=128, description="Matches name, colour, note")]
Upload = Annotated[UploadFile, File(description=f"One of: {', '.join(sorted(IMAGE_TYPES))}")]


async def get_item(item_id: uuid.UUID, user: CurrentUser, db: DbSession) -> WardrobeItem:
    """A wardrobe item of the current user; anyone else's reads as missing."""
    return await wardrobe.owned(db, user.id, item_id)


OwnedItem = Annotated[WardrobeItem, Depends(get_item)]


@router.get("", response_model=WardrobeItemPage, summary="List my wardrobe")
async def list_items(
    user: CurrentUser,
    db: DbSession,
    page: PageParams,
    search: SearchTerm = None,
    category_id: uuid.UUID | None = None,
    formality: Formality | None = None,
) -> WardrobeItemPage:
    return await wardrobe.search(
        db,
        user.id,
        term=search,
        category_id=category_id,
        formality=formality,
        limit=page.limit,
        offset=page.offset,
    )


@router.post(
    "",
    response_model=WardrobeItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a piece I own",
)
async def create_item(
    payload: WardrobeItemCreate, user: CurrentUser, db: DbSession
) -> WardrobeItem:
    return await wardrobe.create(db, payload, user_id=user.id)


@router.post(
    "/from-product",
    response_model=WardrobeItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a catalog product to my wardrobe",
)
async def add_product(
    payload: WardrobeItemFromProduct, user: CurrentUser, db: DbSession
) -> WardrobeItem:
    return await wardrobe.from_product(db, user.id, payload.product_id)


@router.get("/{item_id}", response_model=WardrobeItemRead, summary="Read one piece")
async def read_item(item: OwnedItem) -> WardrobeItem:
    return item


@router.patch("/{item_id}", response_model=WardrobeItemRead, summary="Update a piece")
async def update_item(item: OwnedItem, payload: WardrobeItemUpdate, db: DbSession) -> WardrobeItem:
    return await wardrobe.update(db, item, payload)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove a piece")
async def delete_item(item: OwnedItem, db: DbSession) -> None:
    await wardrobe.delete(db, item)


@router.put("/{item_id}/photo", response_model=WardrobeItemRead, summary="Upload a photo")
async def upload_photo(item: OwnedItem, file: Upload, db: DbSession) -> WardrobeItem:
    return await wardrobe.set_photo(db, item, file)


@router.delete("/{item_id}/photo", response_model=WardrobeItemRead, summary="Remove the photo")
async def remove_photo(item: OwnedItem, db: DbSession) -> WardrobeItem:
    return await wardrobe.remove_photo(db, item)
