from app.services.errors import Conflict, InvalidRequest, PermissionDenied


class EmailAlreadyExists(Conflict):
    pass


class UsernameAlreadyExists(Conflict):
    pass


class InvalidPassword(InvalidRequest):
    pass


class PasswordReuse(Conflict):
    pass


class SelfActionForbidden(PermissionDenied):
    pass
