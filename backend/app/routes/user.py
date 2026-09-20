from fastapi import APIRouter, status

from app.models.user import User
from app.schemas.user import PasswordChange, UserRead, UserUpdate
from app.services.user import profile, users
from core.dependencies import CurrentUser, DbSession

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead, summary="Current authenticated user")
async def read_me(user: CurrentUser) -> User:
    return user


@router.patch("/me", response_model=UserRead, summary="Update the current profile")
async def update_me(payload: UserUpdate, user: CurrentUser, db: DbSession) -> User:
    return await users.update(db, user, payload)


@router.put(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Replace the current password",
)
async def change_my_password(
    payload: PasswordChange, user: CurrentUser, db: DbSession
) -> None:
    await profile.change_password(db, user, payload)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Disable the current account",
)
async def deactivate_me(user: CurrentUser, db: DbSession) -> None:
    await profile.deactivate(db, user)
