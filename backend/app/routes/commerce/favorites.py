import uuid
from fastapi import APIRouter, Request, Response
from app.schemas.commerce import FavoriteRead
from app.services.commerce import favorites as commerce
from app.routes.commerce.dependencies import owner
from core.dependencies import DbSession, OptionalUser

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("", response_model=FavoriteRead)
async def read_favorites(
    request: Request, response: Response, user: OptionalUser, db: DbSession
) -> FavoriteRead:
    user_id, guest_id = owner(request, response, user)
    return await commerce.read_favorites(db, user_id, guest_id)


@router.put("/{product_id}", response_model=FavoriteRead)
async def save_favorite(
    product_id: uuid.UUID,
    request: Request,
    response: Response,
    user: OptionalUser,
    db: DbSession,
) -> FavoriteRead:
    user_id, guest_id = owner(request, response, user)
    return await commerce.set_favorite(db, user_id, guest_id, product_id, True)


@router.delete("/{product_id}", response_model=FavoriteRead)
async def remove_favorite(
    product_id: uuid.UUID,
    request: Request,
    response: Response,
    user: OptionalUser,
    db: DbSession,
) -> FavoriteRead:
    user_id, guest_id = owner(request, response, user)
    return await commerce.set_favorite(db, user_id, guest_id, product_id, False)
