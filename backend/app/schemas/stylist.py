import uuid
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas.base import WriteSchema
from app.schemas.catalog import ProductRead
from utils.enums import Audience, Currency


class OutfitRequest(WriteSchema):
    prompt: Annotated[
        str,
        Field(
            min_length=5,
            max_length=1000,
            examples=["Свидание вечером, на улице +5 и дождь, дресс-код smart casual"],
        ),
    ]
    budget: Annotated[
        Decimal,
        Field(gt=0, max_digits=12, decimal_places=2, examples=["150000"]),
    ]
    audience: Audience | None = Field(
        default=None, description="Only offer items for this audience (and unisex)"
    )


class OutfitItem(BaseModel):
    product: ProductRead
    variant_id: uuid.UUID | None = Field(
        description="Suggested in-stock size; the shopper may pick another"
    )
    price: Decimal
    reason: str | None


class OutfitRead(BaseModel):
    title: str
    summary: str
    items: list[OutfitItem]
    total: Decimal
    budget: Decimal
    currency: Currency = Currency.KZT
    notes: list[str] = Field(
        default=[], description="Why something the shopper asked for is missing"
    )
