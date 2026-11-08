"""Tag products with formality and colour for dress-code checks.

Revision ID: catalog_style_tags
Revises: datam_storefront
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "catalog_style_tags"
down_revision: str | None = "datam_storefront"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("products") as batch:
        batch.add_column(
            sa.Column(
                "formality",
                sa.Enum("casual", "smart_casual", "formal", native_enum=False, name="formality"),
                nullable=True,
            )
        )
        batch.add_column(sa.Column("color", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("products") as batch:
        batch.drop_column("color")
        batch.drop_column("formality")
