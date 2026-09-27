import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.schemas.commerce import (
    AdminOrderPage,
    AdminOrderRead,
    OrderDeliveryUpdate,
    OrderStatusUpdate,
)
from app.services.commerce import admin_orders
from core.dependencies import DbSession, PageParams, require_admin
from utils.enums import OrderStatus

router = APIRouter(
    prefix="/orders",
    tags=["Admin · Orders"],
    dependencies=[Depends(require_admin)],
)

SearchTerm = Annotated[
    str | None,
    Query(max_length=128, description="Matches order ID, recipient name, or phone"),
]


@router.get("", response_model=AdminOrderPage, summary="List and filter orders")
async def list_orders(
    db: DbSession,
    page: PageParams,
    search: SearchTerm = None,
    status: OrderStatus | None = None,
) -> AdminOrderPage:
    return await admin_orders.list_orders(
        db, term=search, status=status, limit=page.limit, offset=page.offset
    )


@router.get("/{order_id}", response_model=AdminOrderRead, summary="Read an order")
async def read_order(order_id: uuid.UUID, db: DbSession) -> AdminOrderRead:
    return await admin_orders.read_order(db, order_id)


@router.patch(
    "/{order_id}", response_model=AdminOrderRead, summary="Update delivery details"
)
async def update_order_delivery(
    order_id: uuid.UUID, payload: OrderDeliveryUpdate, db: DbSession
) -> AdminOrderRead:
    return await admin_orders.update_delivery(db, order_id, payload)


@router.patch(
    "/{order_id}/status",
    response_model=AdminOrderRead,
    summary="Advance or cancel an order",
)
async def update_order_status(
    order_id: uuid.UUID, payload: OrderStatusUpdate, db: DbSession
) -> AdminOrderRead:
    return await admin_orders.update_status(db, order_id, payload.status)
