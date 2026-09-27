import uuid
from fastapi import APIRouter, Request, Response, status
from app.schemas.commerce import CartItemWrite, CartRead, QuantityWrite
from app.services.commerce import cart as commerce
from app.routes.commerce.dependencies import owner
from core.dependencies import DbSession, OptionalUser

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=CartRead)
async def read_cart(
    request: Request, response: Response, user: OptionalUser, db: DbSession
) -> CartRead:
    user_id, guest_id = owner(request, response, user)
    return await commerce.read_cart(db, await commerce.get_cart(db, user_id, guest_id))


@router.post("/items", response_model=CartRead, status_code=status.HTTP_201_CREATED)
async def add_cart_item(
    payload: CartItemWrite,
    request: Request,
    response: Response,
    user: OptionalUser,
    db: DbSession,
) -> CartRead:
    user_id, guest_id = owner(request, response, user)
    cart = await commerce.get_cart(db, user_id, guest_id, create=True)
    assert cart is not None
    return await commerce.add_item(
        db, cart, payload.product_id, payload.variant_id, payload.quantity
    )


@router.patch("/items/{item_id}", response_model=CartRead)
async def change_cart_item(
    item_id: uuid.UUID,
    payload: QuantityWrite,
    request: Request,
    response: Response,
    user: OptionalUser,
    db: DbSession,
) -> CartRead:
    user_id, guest_id = owner(request, response, user)
    cart = await commerce.get_cart(db, user_id, guest_id)
    if cart is None:
        from app.services.errors import NotFound

        raise NotFound("Cart item not found")
    return await commerce.change_item(db, cart, item_id, payload.quantity)


@router.delete("/items/{item_id}", response_model=CartRead)
async def remove_cart_item(
    item_id: uuid.UUID,
    request: Request,
    response: Response,
    user: OptionalUser,
    db: DbSession,
) -> CartRead:
    user_id, guest_id = owner(request, response, user)
    cart = await commerce.get_cart(db, user_id, guest_id)
    if cart is None:
        from app.services.errors import NotFound

        raise NotFound("Cart item not found")
    return await commerce.change_item(db, cart, item_id, None)
