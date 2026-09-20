"""create catalog tables

Revision ID: a890e99d7e81
Revises: ad534676444a
Create Date: 2026-09-20 17:08:47.660139
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a890e99d7e81"
down_revision: str | None = "ad534676444a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIMESTAMP = sa.DateTime(timezone=True)
NOW = sa.text("(CURRENT_TIMESTAMP)")


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", TIMESTAMP, server_default=NOW, nullable=False),
        sa.Column("updated_at", TIMESTAMP, server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
    )
    with op.batch_alter_table("categories", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_categories_slug"), ["slug"], unique=True)

    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "currency",
            sa.Enum(
                "KZT",
                "USD",
                "EUR",
                "RUB",
                name="currency",
                native_enum=False,
                length=3,
            ),
            server_default="KZT",
            nullable=False,
        ),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("stock", sa.Integer(), server_default="0", nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", TIMESTAMP, server_default=NOW, nullable=False),
        sa.Column("updated_at", TIMESTAMP, server_default=NOW, nullable=False),
        sa.CheckConstraint("price >= 0", name=op.f("ck_products_price_not_negative")),
        sa.CheckConstraint("stock >= 0", name=op.f("ck_products_stock_not_negative")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_products_category_id_categories"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
    )
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_products_category_id"), ["category_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_products_sku"), ["sku"], unique=True)
        batch_op.create_index(batch_op.f("ix_products_slug"), ["slug"], unique=True)

    op.create_table(
        "product_variants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("options", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("stock", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", TIMESTAMP, server_default=NOW, nullable=False),
        sa.Column("updated_at", TIMESTAMP, server_default=NOW, nullable=False),
        sa.CheckConstraint(
            "price IS NULL OR price >= 0",
            name=op.f("ck_product_variants_price_not_negative"),
        ),
        sa.CheckConstraint(
            "stock >= 0", name=op.f("ck_product_variants_stock_not_negative")
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_product_variants_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_variants")),
    )
    with op.batch_alter_table("product_variants", schema=None) as batch_op:
        batch_op.create_index(
            "ix_product_variants_product_id_position",
            ["product_id", "position"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_product_variants_sku"), ["sku"], unique=True
        )

    op.create_table(
        "product_images",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("variant_id", sa.Uuid(), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("alt_text", sa.String(length=255), nullable=True),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", TIMESTAMP, server_default=NOW, nullable=False),
        sa.Column("updated_at", TIMESTAMP, server_default=NOW, nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_product_images_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["product_variants.id"],
            name=op.f("fk_product_images_variant_id_product_variants"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_images")),
    )
    with op.batch_alter_table("product_images", schema=None) as batch_op:
        batch_op.create_index(
            "ix_product_images_product_id_position",
            ["product_id", "position"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_product_images_variant_id"), ["variant_id"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("product_images", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_product_images_variant_id"))
        batch_op.drop_index("ix_product_images_product_id_position")

    op.drop_table("product_images")
    with op.batch_alter_table("product_variants", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_product_variants_sku"))
        batch_op.drop_index("ix_product_variants_product_id_position")

    op.drop_table("product_variants")
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_products_slug"))
        batch_op.drop_index(batch_op.f("ix_products_sku"))
        batch_op.drop_index(batch_op.f("ix_products_category_id"))

    op.drop_table("products")
    with op.batch_alter_table("categories", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_categories_slug"))

    op.drop_table("categories")
