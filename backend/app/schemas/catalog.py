import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas.base import Page, ReadSchema, WriteSchema
from utils.enums import Currency

CategoryName = Annotated[str, Field(min_length=2, max_length=128)]
ProductName = Annotated[str, Field(min_length=2, max_length=200)]
VariantName = Annotated[str, Field(min_length=1, max_length=120, examples=["42"])]
Slug = Annotated[
    str,
    Field(
        min_length=2,
        max_length=160,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        examples=["espresso-machine"],
    ),
]
Sku = Annotated[
    str,
    Field(
        min_length=2,
        max_length=64,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
        examples=["COF-1001"],
    ),
]
Price = Annotated[
    Decimal, Field(ge=0, max_digits=12, decimal_places=2, examples=["19990.00"])
]
Stock = Annotated[int, Field(ge=0, examples=[12])]
ImageUrl = Annotated[
    str, Field(min_length=1, max_length=1024, examples=["https://cdn.shop/p/1.jpg"])
]
AltText = Annotated[str | None, Field(max_length=255)]


class CategoryBase(BaseModel):
    name: CategoryName
    description: str | None = None


class CategoryRead(CategoryBase, ReadSchema):
    id: uuid.UUID
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CategoryCreate(CategoryBase, WriteSchema):
    slug: Slug | None = Field(
        default=None, description="Derived from the name when omitted"
    )
    is_active: bool = True


class CategoryUpdate(WriteSchema):
    name: CategoryName | None = None
    slug: Slug | None = None
    description: str | None = None
    is_active: bool | None = None


class ProductImageBase(BaseModel):
    url: ImageUrl
    alt_text: AltText = None


class ProductImageRead(ProductImageBase, ReadSchema):
    id: uuid.UUID
    variant_id: uuid.UUID | None
    position: int
    is_primary: bool


class ProductImageCreate(ProductImageBase, WriteSchema):
    variant_id: uuid.UUID | None = Field(
        default=None, description="Photo of this variant only; shared when omitted"
    )
    position: int | None = Field(
        default=None, ge=0, description="Appended when omitted"
    )
    is_primary: bool = False


class ImageOrder(WriteSchema):
    """Every photo of one gallery, listed in the order it should appear."""

    image_ids: Annotated[list[uuid.UUID], Field(min_length=1)]


class ProductVariantBase(BaseModel):
    name: VariantName
    sku: Sku
    options: dict[str, str] = Field(
        default_factory=dict, examples=[{"size": "42", "color": "black"}]
    )
    price: Price | None = Field(
        default=None, description="Overrides the product price when set"
    )
    stock: Stock = 0


class ProductVariantRead(ProductVariantBase, ReadSchema):
    id: uuid.UUID
    product_id: uuid.UUID
    is_active: bool
    position: int
    images: list[ProductImageRead] = []
    created_at: datetime
    updated_at: datetime


class ProductVariantCreate(ProductVariantBase, WriteSchema):
    is_active: bool = True
    position: int | None = Field(
        default=None, ge=0, description="Appended when omitted"
    )


class ProductVariantUpdate(WriteSchema):
    name: VariantName | None = None
    sku: Sku | None = None
    options: dict[str, str] | None = None
    price: Price | None = None
    stock: Stock | None = None
    is_active: bool | None = None
    position: Annotated[int, Field(ge=0)] | None = None


class ProductBase(BaseModel):
    name: ProductName
    description: str | None = None
    price: Price
    currency: Currency = Currency.KZT
    sku: Sku
    stock: Stock = 0


class ProductRead(ProductBase, ReadSchema):
    id: uuid.UUID
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    total_stock: int
    category: CategoryRead
    images: list[ProductImageRead] = []
    variants: list[ProductVariantRead] = []


class ProductCreate(ProductBase, WriteSchema):
    category_id: uuid.UUID
    slug: Slug | None = Field(
        default=None, description="Derived from the name when omitted"
    )
    is_active: bool = True
    images: list[ProductImageCreate] = []
    variants: list[ProductVariantCreate] = []


class ProductUpdate(WriteSchema):
    name: ProductName | None = None
    description: str | None = None
    price: Price | None = None
    currency: Currency | None = None
    sku: Sku | None = None
    stock: Stock | None = None
    category_id: uuid.UUID | None = None
    slug: Slug | None = None
    is_active: bool | None = None


CategoryPage = Page[CategoryRead]
ProductPage = Page[ProductRead]
