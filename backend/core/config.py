from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DEV_SECRET_KEY = "dev-secret-change-me"
MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    PROJECT_NAME: str = "Datam Backend"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    DATABASE_URL: str
    DB_ECHO: bool = False

    MEDIA_ROOT: Path = BASE_DIR / "media"
    MEDIA_URL: str = "/media"
    MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024

    SECRET_KEY: str = DEV_SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = False

    OLLAMA_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen3.5:2b"
    OLLAMA_TIMEOUT_SECONDS: float = Field(default=120, gt=0, le=120)
    STYLIST_MAX_CANDIDATES: int = Field(default=40, ge=1, le=100)

    CORS_ORIGINS: Annotated[list[str], NoDecode] = []

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _require_real_secret_outside_debug(self) -> "Settings":
        weak = self.SECRET_KEY == DEV_SECRET_KEY or len(self.SECRET_KEY) < MIN_SECRET_KEY_LENGTH
        if weak and not self.DEBUG:
            raise ValueError(
                f"SECRET_KEY must be a random string of at least {MIN_SECRET_KEY_LENGTH} "
                "characters when DEBUG is off (openssl rand -hex 32)"
            )
        return self

    @property
    def sync_database_url(self) -> str:
        return self.DATABASE_URL.replace("+asyncpg", "")

    @property
    def access_token_expire_seconds(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
