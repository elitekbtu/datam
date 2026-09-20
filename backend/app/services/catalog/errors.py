from app.services.errors import Conflict, InvalidRequest, NotFound


class SlugAlreadyExists(Conflict):
    pass


class SkuAlreadyExists(Conflict):
    pass


class CategoryInUse(Conflict):
    pass


class VariantNotFound(NotFound):
    pass


class ImageNotFound(NotFound):
    pass


class InvalidImageOrder(InvalidRequest):
    pass
