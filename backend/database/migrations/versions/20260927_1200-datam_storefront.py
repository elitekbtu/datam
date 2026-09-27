"""Add customer sessions, shopping data and fashion taxonomy.

Revision ID: datam_storefront
Revises: a890e99d7e81
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "datam_storefront"
down_revision: str | None = "a890e99d7e81"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NOW = sa.text("(CURRENT_TIMESTAMP)")
TIMESTAMP = sa.DateTime(timezone=True)


def upgrade() -> None:
    with op.batch_alter_table("categories") as batch:
        batch.add_column(sa.Column("parent_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_categories_parent_id_categories",
            "categories",
            ["parent_id"],
            ["id"],
            ondelete="RESTRICT",
        )
    with op.batch_alter_table("products") as batch:
        batch.add_column(
            sa.Column(
                "audience",
                sa.Enum("women", "men", "unisex", native_enum=False, name="audience"),
                server_default="unisex",
                nullable=False,
            )
        )

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("refresh_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", TIMESTAMP, nullable=False),
        sa.Column("revoked_at", TIMESTAMP, nullable=True),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])

    op.create_table(
        "carts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            unique=True,
            nullable=True,
        ),
        sa.Column("guest_id", sa.Uuid(), unique=True, nullable=True),
        sa.Column("created_at", TIMESTAMP, server_default=NOW, nullable=False),
        sa.Column("updated_at", TIMESTAMP, server_default=NOW, nullable=False),
    )
    op.create_table(
        "cart_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "cart_id",
            sa.Uuid(),
            sa.ForeignKey("carts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Uuid(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "variant_id",
            sa.Uuid(),
            sa.ForeignKey("product_variants.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
    )
    op.create_index("ix_cart_items_cart_id", "cart_items", ["cart_id"])

    op.create_table(
        "favorites",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("guest_id", sa.Uuid(), nullable=True),
        sa.Column(
            "product_id",
            sa.Uuid(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_favorites_user_product", "favorites", ["user_id", "product_id"], unique=True
    )
    op.create_index(
        "ix_favorites_guest_product",
        "favorites",
        ["guest_id", "product_id"],
        unique=True,
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(24), server_default="placed", nullable=False),
        sa.Column("full_name", sa.String(128), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("city", sa.String(128), nullable=False),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column("postal_code", sa.String(16), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="KZT", nullable=False),
        sa.Column("created_at", TIMESTAMP, server_default=NOW, nullable=False),
        sa.Column("updated_at", TIMESTAMP, server_default=NOW, nullable=False),
    )
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_index(
        "ix_orders_user_idempotency",
        "orders",
        ["user_id", "idempotency_key"],
        unique=True,
    )
    op.create_table(
        "order_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "order_id",
            sa.Uuid(),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("variant_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("image_url", sa.String(1024), nullable=True),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("favorites")
    op.drop_table("cart_items")
    op.drop_table("carts")
    op.drop_table("auth_sessions")
    with op.batch_alter_table("products") as batch:
        batch.drop_column("audience")
    with op.batch_alter_table("categories") as batch:
        batch.drop_constraint("fk_categories_parent_id_categories", type_="foreignkey")
        batch.drop_column("parent_id")
