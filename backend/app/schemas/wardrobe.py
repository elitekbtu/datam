import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas.base import Page, ReadSchema, WriteSchema
from utils.enums import Formality

ItemName = Annotated[str, Field(min_length=1, max_length=200, examples=["Белая рубашка"])]
Color = Annotated[str | None, Field(max_length=64, examples=["white"])]
Note = Annotated[str | None, Field(max_length=1000)]


class WardrobeItemBase(BaseModel):
    name: ItemName
    category_id: uuid.UUID | None = None
    formality: Formality | None = None
    color: Color = None
    note: Note = None


class WardrobeItemRead(WardrobeItemBase, ReadSchema):
    id: uuid.UUID
    product_id: uuid.UUID | None
    image_url: str | None
    created_at: datetime
    updated_at: datetime


class WardrobeItemCreate(WardrobeItemBase, WriteSchema):
    pass


class WardrobeItemUpdate(WriteSchema):
    name: ItemName | None = None
    category_id: uuid.UUID | None = None
    formality: Formality | None = None
    color: Color = None
    note: Note = None


class WardrobeItemFromProduct(WriteSchema):
    product_id: uuid.UUID


WardrobeItemPage = Page[WardrobeItemRead]
