import uuid
from fastapi import Request, Response
from core.cookies import GUEST_COOKIE, set_guest_cookie
from core.dependencies import OptionalUser


def owner(
    request: Request, response: Response, user: OptionalUser
) -> tuple[uuid.UUID | None, uuid.UUID | None]:
    if user:
        return user.id, None
    try:
        guest_id = uuid.UUID(request.cookies.get(GUEST_COOKIE, ""))
    except ValueError:
        guest_id = uuid.uuid4()
        set_guest_cookie(response, str(guest_id))
    return None, guest_id
