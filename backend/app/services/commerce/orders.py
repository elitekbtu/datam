import uuid
from decimal import Decimal
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.catalog import Product, ProductVariant
from app.models.commerce import Order, OrderItem
from app.schemas.commerce import OrderCreate, OrderPage, OrderRead
from app.services.commerce.cart import get_cart
from app.services.commerce.common import get_product, variant_for, image_for, price_for
from app.services.errors import Conflict, InvalidRequest, NotFound
from utils.enums import Currency


async def create_order(
    db: AsyncSession, user_id: uuid.UUID, payload: OrderCreate, key: str
) -> OrderRead:
    prior = (
        (
            await db.scalars(
                select(Order).where(
                    Order.user_id == user_id, Order.idempotency_key == key
                )
            )
        )
        .unique()
        .one_or_none()
    )
    if prior:
        return OrderRead.model_validate(prior)
    cart = await get_cart(db, user_id, None)
    if cart is None or not cart.items:
        raise InvalidRequest("Cart is empty")
    order = Order(
        user_id=user_id,
        idempotency_key=key,
        **payload.model_dump(),
        subtotal=Decimal("0"),
        total=Decimal("0"),
        currency="KZT",
    )
    db.add(order)
    await db.flush()
    subtotal = Decimal("0")
    for item in cart.items:
        product = await get_product(db, item.product_id)
        variant = variant_for(product, item.variant_id)
        if product.currency != Currency.KZT:
            raise InvalidRequest("Checkout currently supports KZT products only")
        model = ProductVariant if variant else Product
        target_id = variant.id if variant else product.id
        changed = await db.execute(
            update(model)
            .where(model.id == target_id, model.stock >= item.quantity)
            .values(stock=model.stock - item.quantity)
        )
        if changed.rowcount != 1:
            await db.rollback()
            raise Conflict("An item is out of stock; review your cart")
        unit = price_for(product, variant)
        line_total = unit * item.quantity
        subtotal += line_total
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                variant_id=variant.id if variant else None,
                name=product.name,
                sku=variant.sku if variant else product.sku,
                options=variant.options if variant else {},
                image_url=image_for(product, variant),
                unit_price=unit,
                quantity=item.quantity,
                total=line_total,
            )
        )
        await db.delete(item)
    order.subtotal = subtotal
    order.total = subtotal
    await db.commit()
    loaded = (
        (await db.scalars(select(Order).where(Order.id == order.id))).unique().one()
    )
    return OrderRead.model_validate(loaded)


async def list_orders(
    db: AsyncSession, user_id: uuid.UUID, limit: int, offset: int
) -> OrderPage:
    total = (
        await db.scalar(
            select(func.count()).select_from(Order).where(Order.user_id == user_id)
        )
        or 0
    )
    orders = (
        (
            await db.scalars(
                select(Order)
                .where(Order.user_id == user_id)
                .order_by(Order.created_at.desc(), Order.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .unique()
        .all()
    )
    return OrderPage(
        items=[OrderRead.model_validate(row) for row in orders],
        total=total,
        limit=limit,
        offset=offset,
    )


async def read_order(
    db: AsyncSession, user_id: uuid.UUID, order_id: uuid.UUID
) -> OrderRead:
    order = (
        (
            await db.scalars(
                select(Order).where(Order.id == order_id, Order.user_id == user_id)
            )
        )
        .unique()
        .one_or_none()
    )
    if order is None:
        raise NotFound("Order not found")
    return OrderRead.model_validate(order)
