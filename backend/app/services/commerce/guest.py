import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.catalog import Product
from app.models.commerce import CartItem, Favorite
from app.services.commerce.cart import get_cart


async def merge_guest(db: AsyncSession, raw_guest_id: str, user_id: uuid.UUID) -> None:
    try:
        guest_id = uuid.UUID(raw_guest_id)
    except ValueError:
        return
    guest = await get_cart(db, None, guest_id)
    if guest:
        owned = await get_cart(db, user_id, None, create=True)
        assert owned is not None
        for item in guest.items:
            existing = next(
                (
                    row
                    for row in owned.items
                    if row.product_id == item.product_id
                    and row.variant_id == item.variant_id
                ),
                None,
            )
            product = await db.get(Product, item.product_id)
            if product is None or not product.is_active:
                continue
            variant = (
                next(
                    (
                        v
                        for v in product.variants
                        if v.id == item.variant_id and v.is_active
                    ),
                    None,
                )
                if item.variant_id
                else None
            )
            stock = variant.stock if variant else product.stock
            quantity = min(
                stock, item.quantity + (existing.quantity if existing else 0), 99
            )
            if quantity < 1:
                continue
            if existing:
                existing.quantity = quantity
            else:
                db.add(
                    CartItem(
                        cart_id=owned.id,
                        product_id=item.product_id,
                        variant_id=item.variant_id,
                        quantity=quantity,
                    )
                )
        await db.delete(guest)
    guest_favs = (
        await db.scalars(select(Favorite).where(Favorite.guest_id == guest_id))
    ).all()
    owned_favs = set(
        (
            await db.scalars(
                select(Favorite.product_id).where(Favorite.user_id == user_id)
            )
        ).all()
    )
    for favorite in guest_favs:
        if favorite.product_id not in owned_favs:
            db.add(Favorite(user_id=user_id, product_id=favorite.product_id))
            owned_favs.add(favorite.product_id)
        await db.delete(favorite)
    await db.commit()
