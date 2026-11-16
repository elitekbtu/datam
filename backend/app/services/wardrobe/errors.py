from app.services.errors import InvalidRequest, NotFound


class WardrobeItemNotFound(NotFound):
    pass


class UnknownCategory(InvalidRequest):
    pass
