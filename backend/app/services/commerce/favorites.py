import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.catalog import Product
from app.models.commerce import Favorite
from app.schemas.catalog import ProductRead
from app.schemas.commerce import FavoriteRead
from app.services.commerce.common import get_product


async def read_favorites(
    db: AsyncSession, user_id: uuid.UUID | None, guest_id: uuid.UUID | None
) -> FavoriteRead:
    condition = (
        Favorite.user_id == user_id if user_id else Favorite.guest_id == guest_id
    )
    ids = (await db.scalars(select(Favorite.product_id).where(condition))).all()
    if not ids:
        return FavoriteRead(items=[])
    products = (
        (
            await db.scalars(
                select(Product).where(Product.id.in_(ids), Product.is_active.is_(True))
            )
        )
        .unique()
        .all()
    )
    return FavoriteRead(items=[ProductRead.model_validate(p) for p in products])


async def set_favorite(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    guest_id: uuid.UUID | None,
    product_id: uuid.UUID,
    enabled: bool,
) -> FavoriteRead:
    condition = (
        Favorite.user_id == user_id if user_id else Favorite.guest_id == guest_id
    )
    current = await db.scalar(
        select(Favorite).where(condition, Favorite.product_id == product_id)
    )
    if enabled and current is None:
        await get_product(db, product_id)
        db.add(
            Favorite(
                user_id=user_id,
                guest_id=None if user_id else guest_id,
                product_id=product_id,
            )
        )
    elif not enabled and current is not None:
        await db.delete(current)
    await db.commit()
    return await read_favorites(db, user_id, guest_id)
