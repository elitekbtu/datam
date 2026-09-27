"""Order lookup and fulfillment actions for administrators."""

import uuid
from typing import Final

from sqlalchemy import String, cast, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Product, ProductVariant
from app.models.commerce import Order
from app.schemas.commerce import AdminOrderPage, AdminOrderRead, OrderDeliveryUpdate
from app.services.errors import Conflict, NotFound
from utils.enums import OrderStatus

NEXT_STATUSES: Final = {
    OrderStatus.PLACED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


async def list_orders(
    db: AsyncSession,
    *,
    term: str | None = None,
    status: OrderStatus | None = None,
    limit: int,
    offset: int,
) -> AdminOrderPage:
    conditions = []
    if term and (needle := term.strip().lower()):
        search = f"%{needle}%"
        matches = [
            func.lower(Order.full_name).like(search),
            func.lower(Order.phone).like(search),
            cast(Order.id, String).ilike(f"{needle}%"),
        ]
        conditions.append(or_(*matches))
    if status is not None:
        conditions.append(Order.status == status.value)

    total = (
        await db.scalar(select(func.count()).select_from(Order).where(*conditions)) or 0
    )
    rows = (
        (
            await db.scalars(
                select(Order)
                .where(*conditions)
                .order_by(Order.created_at.desc(), Order.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .unique()
        .all()
    )
    return AdminOrderPage(
        items=[AdminOrderRead.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


async def read_order(db: AsyncSession, order_id: uuid.UUID) -> AdminOrderRead:
    order = (
        (await db.scalars(select(Order).where(Order.id == order_id)))
        .unique()
        .one_or_none()
    )
    if order is None:
        raise NotFound("Order not found")
    return AdminOrderRead.model_validate(order)


async def update_delivery(
    db: AsyncSession, order_id: uuid.UUID, payload: OrderDeliveryUpdate
) -> AdminOrderRead:
    order = (
        (await db.scalars(select(Order).where(Order.id == order_id).with_for_update()))
        .unique()
        .one_or_none()
    )
    if order is None:
        raise NotFound("Order not found")
    if order.status not in {OrderStatus.PLACED, OrderStatus.PROCESSING}:
        raise Conflict("Delivery details cannot be changed after shipping")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is None and field not in {"postal_code", "note"}:
            continue
        setattr(order, field, value.strip() if isinstance(value, str) else value)
    if changes:
        await db.commit()
    return AdminOrderRead.model_validate(order)


async def update_status(
    db: AsyncSession, order_id: uuid.UUID, status: OrderStatus
) -> AdminOrderRead:
    order = (
        (await db.scalars(select(Order).where(Order.id == order_id).with_for_update()))
        .unique()
        .one_or_none()
    )
    if order is None:
        raise NotFound("Order not found")
    if order.status == status:
        return AdminOrderRead.model_validate(order)
    if status not in NEXT_STATUSES[OrderStatus(order.status)]:
        raise Conflict("This order status change is not allowed")

    if status is OrderStatus.CANCELLED:
        for item in order.items:
            model = ProductVariant if item.variant_id else Product
            target_id = item.variant_id or item.product_id
            await db.execute(
                update(model)
                .where(model.id == target_id)
                .values(stock=model.stock + item.quantity)
            )

    order.status = status.value
    await db.commit()
    return AdminOrderRead.model_validate(order)
