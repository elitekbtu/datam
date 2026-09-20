from fastapi import APIRouter, status

from app.models.user import User
from app.schemas.user import PasswordChange, UserRead, UserUpdate
from app.services.user import profile, users
from core.dependencies import CurrentUser, DbSession

router = APIRouter(prefix="/account", tags=["Account"])


@router.get("", response_model=UserRead, summary="Current authenticated user")
async def read_account(user: CurrentUser) -> User:
    return user


@router.patch("", response_model=UserRead, summary="Update the current profile")
async def update_account(payload: UserUpdate, user: CurrentUser, db: DbSession) -> User:
    return await users.update(db, user, payload)


@router.put(
    "/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Replace the current password",
)
async def change_password(
    payload: PasswordChange, user: CurrentUser, db: DbSession
) -> None:
    await profile.change_password(db, user, payload)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Disable the current account",
)
async def deactivate_account(user: CurrentUser, db: DbSession) -> None:
    await profile.deactivate(db, user)
