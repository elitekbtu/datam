"""Let users keep a wardrobe of clothes they already own.

Revision ID: wardrobe_items
Revises: catalog_style_tags
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "wardrobe_items"
down_revision: str | None = "catalog_style_tags"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NOW = sa.text("(CURRENT_TIMESTAMP)")
TIMESTAMP = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "wardrobe_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "category_id",
            sa.Uuid(),
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "product_id",
            sa.Uuid(),
            sa.ForeignKey("products.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "formality",
            sa.Enum("casual", "smart_casual", "formal", native_enum=False, name="formality"),
            nullable=True,
        ),
        sa.Column("color", sa.String(64), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(1024), nullable=True),
        sa.Column("created_at", TIMESTAMP, server_default=NOW, nullable=False),
        sa.Column("updated_at", TIMESTAMP, server_default=NOW, nullable=False),
    )
    op.create_index("ix_wardrobe_items_user_id", "wardrobe_items", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_wardrobe_items_user_id", table_name="wardrobe_items")
    op.drop_table("wardrobe_items")
