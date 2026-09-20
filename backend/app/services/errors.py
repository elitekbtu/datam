class ServiceError(Exception):
    """Base class for failures a route turns into an error response."""


class NotFound(ServiceError):
    pass


class Conflict(ServiceError):
    pass


class PermissionDenied(ServiceError):
    pass


class Unauthenticated(ServiceError):
    pass


class InvalidRequest(ServiceError):
    pass
