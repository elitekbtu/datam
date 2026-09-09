from enum import StrEnum


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"
