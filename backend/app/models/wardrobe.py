import uuid

from sqlalchemy import Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin
from utils.enums import Formality


class WardrobeItem(Base, TimestampMixin):
    """A piece of clothing the user already owns, bought here or elsewhere."""

    __tablename__ = "wardrobe_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    formality: Mapped[Formality | None] = mapped_column(
        Enum(
            Formality,
            name="formality",
            native_enum=False,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=True,
    )
    color: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    def __repr__(self) -> str:
        return f"<WardrobeItem id={self.id} name={self.name!r}>"
