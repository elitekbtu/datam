from app.services.errors import PermissionDenied, Unauthenticated


class InvalidCredentials(Unauthenticated):
    pass


class InactiveUser(PermissionDenied):
    pass
