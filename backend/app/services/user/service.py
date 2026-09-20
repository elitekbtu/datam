from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.base import Page
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.base import DEFAULT_PAGE_SIZE, CRUDService
from app.services.user.errors import EmailAlreadyExists, UsernameAlreadyExists
from core.security import hash_password
from utils.enums import UserRole


class UserService(CRUDService[User, UserRead, UserCreate, UserUpdate]):
    """Storage for accounts: normalised identities, hashed passwords."""

    model = User
    read_schema = UserRead
    nullable_fields = frozenset({"full_name"})
    order_by = (User.created_at.desc(), User.id)
    not_found_message = "User not found"

    async def prepare(
        self,
        db: AsyncSession,
        changes: dict[str, Any],
        instance: User | None = None,
    ) -> dict[str, Any]:
        if (email := changes.get("email")) is not None:
            changes["email"] = email.strip().lower()
        if (username := changes.get("username")) is not None:
            changes["username"] = username.strip()
        if (password := changes.pop("password", None)) is not None:
            changes["hashed_password"] = hash_password(password)
        await self.ensure_identity_free(db, changes, instance)
        return changes

    async def ensure_identity_free(
        self,
        db: AsyncSession,
        changes: dict[str, Any],
        instance: User | None = None,
    ) -> None:
        """Reject an email or username another account already holds."""
        email = changes.get("email")
        username = changes.get("username")

        conditions = []
        if email is not None:
            conditions.append(func.lower(User.email) == email)
        if username is not None:
            conditions.append(func.lower(User.username) == username.lower())
        if not conditions:
            return

        stmt = select(User).where(or_(*conditions))
        if instance is not None:
            stmt = stmt.where(User.id != instance.id)

        taken = await db.scalar(stmt)
        if taken is None:
            return
        if email is not None and taken.email.lower() == email:
            raise EmailAlreadyExists("An account with this email already exists")
        raise UsernameAlreadyExists("This username is already taken")

    async def by_email(self, db: AsyncSession, email: str) -> User | None:
        stmt = select(User).where(func.lower(User.email) == email.strip().lower())
        return await db.scalar(stmt)

    async def search(
        self,
        db: AsyncSession,
        *,
        term: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> Page[UserRead]:
        conditions = []
        if term and (needle := f"%{term.strip().lower()}%"):
            conditions.append(
                or_(
                    func.lower(User.email).like(needle),
                    func.lower(User.username).like(needle),
                    func.lower(User.full_name).like(needle),
                )
            )
        if role is not None:
            conditions.append(User.role == role)
        if is_active is not None:
            conditions.append(User.is_active.is_(is_active))
        return await self.paginate(db, *conditions, limit=limit, offset=offset)


users = UserService()
