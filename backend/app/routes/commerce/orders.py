import uuid
from typing import Annotated
from fastapi import APIRouter, Header, status
from app.schemas.commerce import OrderCreate, OrderPage, OrderRead
from app.services.commerce import orders as commerce
from core.dependencies import CurrentUser, DbSession, PageParams

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def place_order(
    payload: OrderCreate,
    user: CurrentUser,
    db: DbSession,
    idempotency_key: Annotated[str, Header(min_length=8, max_length=128)],
) -> OrderRead:
    return await commerce.create_order(db, user.id, payload, idempotency_key)


@router.get("", response_model=OrderPage)
async def list_orders(user: CurrentUser, db: DbSession, page: PageParams) -> OrderPage:
    return await commerce.list_orders(db, user.id, page.limit, page.offset)


@router.get("/{order_id}", response_model=OrderRead)
async def read_order(
    order_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> OrderRead:
    return await commerce.read_order(db, user.id, order_id)
