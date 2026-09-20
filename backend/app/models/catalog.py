import uuid
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin
from utils.enums import Currency


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(160), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Category id={self.id} slug={self.slug!r}>"


class Product(Base, TimestampMixin):
    """One catalog item — a model of shoes, not a single size of it."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price >= 0", name="price_not_negative"),
        CheckConstraint("stock >= 0", name="stock_not_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(220), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(
        Enum(
            Currency,
            name="currency",
            native_enum=False,
            length=3,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=Currency.KZT,
        server_default=Currency.KZT.value,
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    stock: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category: Mapped[Category] = relationship(lazy="joined")
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductVariant.position",
        lazy="selectin",
    )
    gallery: Mapped[list["ProductImage"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.position",
        lazy="selectin",
    )

    @property
    def images(self) -> list["ProductImage"]:
        """Photos of the product itself; a variant's own photos stay with it."""
        return [image for image in self.gallery if image.variant_id is None]

    @property
    def total_stock(self) -> int:
        """Units on hand — summed over active variants once the product has any."""
        if not self.variants:
            return self.stock
        return sum(variant.stock for variant in self.variants if variant.is_active)

    @property
    def in_stock(self) -> bool:
        return self.total_stock > 0

    def __repr__(self) -> str:
        return f"<Product id={self.id} sku={self.sku!r} price={self.price}>"


class ProductVariant(Base, TimestampMixin):
    """A single buyable flavour of a product: one size, one colour, one SKU."""

    __tablename__ = "product_variants"
    __table_args__ = (
        CheckConstraint("stock >= 0", name="stock_not_negative"),
        CheckConstraint("price IS NULL OR price >= 0", name="price_not_negative"),
        Index("ix_product_variants_product_id_position", "product_id", "position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sku: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    options: Mapped[dict[str, str]] = mapped_column(
        JSON, default=dict, server_default="{}", nullable=False
    )
    #: Overrides the product price when set.
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    stock: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    position: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )

    product: Mapped[Product] = relationship(back_populates="variants")
    images: Mapped[list["ProductImage"]] = relationship(
        order_by="ProductImage.position",
        lazy="selectin",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<ProductVariant id={self.id} sku={self.sku!r} name={self.name!r}>"


class ProductImage(Base, TimestampMixin):
    """A photo of a product, or of one of its variants when ``variant_id`` is set."""

    __tablename__ = "product_images"
    __table_args__ = (
        Index("ix_product_images_product_id_position", "product_id", "position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False
    )

    product: Mapped[Product] = relationship(back_populates="gallery")

    def __repr__(self) -> str:
        return f"<ProductImage id={self.id} position={self.position}>"
