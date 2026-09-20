import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.models.user import User
from app.schemas.user import AdminUserCreate, AdminUserUpdate, UserPage, UserRead
from app.services.user import admin as user_admin
from app.services.user import users
from core.dependencies import CurrentAdmin, DbSession, PageParams, require_admin
from utils.enums import UserRole

router = APIRouter(
    prefix="/users",
    tags=["Admin · Users"],
    dependencies=[Depends(require_admin)],
)

SearchTerm = Annotated[
    str | None,
    Query(max_length=128, description="Matches email, username, or full name"),
]


@router.get("", response_model=UserPage, summary="List and filter accounts")
async def list_users(
    db: DbSession,
    page: PageParams,
    search: SearchTerm = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
) -> UserPage:
    return await users.search(
        db,
        term=search,
        role=role,
        is_active=is_active,
        limit=page.limit,
        offset=page.offset,
    )


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Provision an account",
)
async def create_user(payload: AdminUserCreate, db: DbSession) -> User:
    return await users.create(db, payload)


@router.get("/{user_id}", response_model=UserRead, summary="Read a single account")
async def read_user(user_id: uuid.UUID, db: DbSession) -> User:
    return await users.require(db, user_id)


@router.patch("/{user_id}", response_model=UserRead, summary="Update any account")
async def update_user(
    user_id: uuid.UUID,
    payload: AdminUserUpdate,
    admin: CurrentAdmin,
    db: DbSession,
) -> User:
    user = await users.require(db, user_id)
    return await user_admin.update(db, user, payload, actor=admin)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently remove an account",
)
async def delete_user(
    user_id: uuid.UUID, admin: CurrentAdmin, db: DbSession
) -> None:
    user = await users.require(db, user_id)
    await user_admin.delete(db, user, actor=admin)
