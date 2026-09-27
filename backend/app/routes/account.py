from fastapi import APIRouter, Response, status

from app.models.user import User
from app.schemas.user import PasswordChange, UserRead, UserUpdate
from app.services.user import profile, users
from app.services.auth.sessions import revoke_all
from core.cookies import clear_auth_cookies
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
    payload: PasswordChange, user: CurrentUser, db: DbSession, response: Response
) -> None:
    await profile.change_password(db, user, payload)
    await revoke_all(db, user.id)
    clear_auth_cookies(response)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Disable the current account",
)
async def deactivate_account(user: CurrentUser, db: DbSession, response: Response) -> None:
    await profile.deactivate(db, user)
    await revoke_all(db, user.id)
    clear_auth_cookies(response)
