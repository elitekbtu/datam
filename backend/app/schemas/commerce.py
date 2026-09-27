import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas.catalog import ProductRead
from app.schemas.base import ReadSchema, WriteSchema


class CartItemWrite(WriteSchema):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: Annotated[int, Field(ge=1, le=99)] = 1


class QuantityWrite(WriteSchema):
    quantity: Annotated[int, Field(ge=1, le=99)]


class CartItemRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    slug: str
    name: str
    sku: str
    options: dict[str, str]
    image_url: str | None
    unit_price: Decimal
    quantity: int
    total: Decimal
    available: bool
    stock: int
    currency: str


class CartRead(BaseModel):
    items: list[CartItemRead]
    total: Decimal
    count: int


class FavoriteRead(BaseModel):
    items: list[ProductRead]


class OrderCreate(WriteSchema):
    full_name: Annotated[str, Field(min_length=2, max_length=128)]
    phone: Annotated[str, Field(min_length=7, max_length=32)]
    city: Annotated[str, Field(min_length=2, max_length=128)]
    address: Annotated[str, Field(min_length=5, max_length=255)]
    postal_code: Annotated[str | None, Field(max_length=16)] = None
    note: Annotated[str | None, Field(max_length=1000)] = None


class OrderItemRead(ReadSchema):
    id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    name: str
    sku: str
    options: dict[str, str]
    image_url: str | None
    unit_price: Decimal
    quantity: int
    total: Decimal


class OrderRead(ReadSchema):
    id: uuid.UUID
    status: str
    full_name: str
    phone: str
    city: str
    address: str
    postal_code: str | None
    note: str | None
    subtotal: Decimal
    total: Decimal
    currency: str
    items: list[OrderItemRead]
    created_at: datetime


class OrderPage(BaseModel):
    items: list[OrderRead]
    total: int
    limit: int
    offset: int
