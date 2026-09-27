import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.catalog import Product
from app.models.commerce import Cart, CartItem
from app.schemas.commerce import CartItemRead, CartRead
from app.services.commerce.common import get_product, variant_for, image_for, price_for
from app.services.errors import Conflict, NotFound


async def get_cart(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    guest_id: uuid.UUID | None,
    *,
    create: bool = False,
) -> Cart | None:
    condition = Cart.user_id == user_id if user_id else Cart.guest_id == guest_id
    cart = (
        (
            await db.scalars(
                select(Cart).where(condition).execution_options(populate_existing=True)
            )
        )
        .unique()
        .one_or_none()
    )
    if cart is None and create:
        cart = Cart(user_id=user_id, guest_id=None if user_id else guest_id, items=[])
        db.add(cart)
        await db.commit()
    return cart


async def read_cart(db: AsyncSession, cart: Cart | None) -> CartRead:
    if cart is None or not cart.items:
        return CartRead(items=[], total=Decimal("0"), count=0)
    ids = {item.product_id for item in cart.items}
    products = {
        product.id: product
        for product in (
            await db.scalars(select(Product).where(Product.id.in_(ids)))
        ).unique()
    }
    rows: list[CartItemRead] = []
    for item in cart.items:
        product = products.get(item.product_id)
        if product is None:
            continue
        variant = next((v for v in product.variants if v.id == item.variant_id), None)
        stock = variant.stock if variant else product.stock
        available = bool(
            product.is_active
            and product.category.is_active
            and (variant is None or variant.is_active)
            and stock >= item.quantity
            and stock > 0
        )
        unit = price_for(product, variant)
        rows.append(
            CartItemRead(
                id=item.id,
                product_id=product.id,
                variant_id=item.variant_id,
                slug=product.slug,
                name=product.name,
                sku=variant.sku if variant else product.sku,
                options=variant.options if variant else {},
                image_url=image_for(product, variant),
                unit_price=unit,
                quantity=item.quantity,
                total=unit * item.quantity,
                available=available,
                stock=stock,
                currency=product.currency.value,
            )
        )
    return CartRead(
        items=rows,
        total=sum((row.total for row in rows), Decimal("0")),
        count=sum(row.quantity for row in rows),
    )


async def add_item(
    db: AsyncSession,
    cart: Cart,
    product_id: uuid.UUID,
    variant_id: uuid.UUID | None,
    quantity: int,
) -> CartRead:
    product = await get_product(db, product_id)
    variant = variant_for(product, variant_id)
    stock = variant.stock if variant else product.stock
    existing = next(
        (
            item
            for item in cart.items
            if item.product_id == product_id and item.variant_id == variant_id
        ),
        None,
    )
    wanted = quantity + (existing.quantity if existing else 0)
    if wanted > stock:
        raise Conflict("Requested quantity exceeds available stock")
    if existing:
        existing.quantity = wanted
    else:
        db.add(
            CartItem(
                cart_id=cart.id,
                product_id=product_id,
                variant_id=variant_id,
                quantity=quantity,
            )
        )
    await db.commit()
    return await read_cart(db, await get_cart(db, cart.user_id, cart.guest_id))


async def change_item(
    db: AsyncSession, cart: Cart, item_id: uuid.UUID, quantity: int | None
) -> CartRead:
    item = next((row for row in cart.items if row.id == item_id), None)
    if item is None:
        raise NotFound("Cart item not found")
    if quantity is None:
        await db.delete(item)
    else:
        product = await get_product(db, item.product_id)
        variant = variant_for(product, item.variant_id)
        if quantity > (variant.stock if variant else product.stock):
            raise Conflict("Requested quantity exceeds available stock")
        item.quantity = quantity
    await db.commit()
    return await read_cart(db, await get_cart(db, cart.user_id, cart.guest_id))
