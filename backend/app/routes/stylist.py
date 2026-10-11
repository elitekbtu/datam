from fastapi import APIRouter, Depends

from app.schemas.stylist import OutfitRead, OutfitRequest
from app.services import stylist
from core.dependencies import DbSession, get_current_user

# Signed-in shoppers only, so anonymous traffic cannot tie up the model.
router = APIRouter(
    prefix="/stylist",
    tags=["AI Stylist"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/outfit",
    response_model=OutfitRead,
    summary="Put together an outfit from the catalog for an occasion and budget",
)
async def suggest_outfit(payload: OutfitRequest, db: DbSession) -> OutfitRead:
    return await stylist.suggest(db, payload)
