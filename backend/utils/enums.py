from enum import StrEnum


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class Currency(StrEnum):
    KZT = "KZT"
    USD = "USD"
    EUR = "EUR"
    RUB = "RUB"


class ProductSort(StrEnum):
    NEWEST = "newest"
    OLDEST = "oldest"
    NAME = "name"
    NAME_DESC = "name_desc"
    PRICE = "price"
    PRICE_DESC = "price_desc"
