"""Application configuration.

Loads settings from environment variables and the repository-root ``.env`` file
using ``pydantic-settings``. Real secrets must only ever be provided through
the environment or a local ``.env`` file (which is git-ignored); only safe
placeholder values belong in ``.env.example``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository layout (this file is backend/app/core/config.py):
#   parents[0] -> backend/app/core
#   parents[1] -> backend/app
#   parents[2] -> backend
#   parents[3] -> repository root
BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[3]

# Placeholder values that must never be used as real secrets in production.
_UNSAFE_PLACEHOLDERS = {"change_me", "changeme", "", "secret", "test"}


class Settings(BaseSettings):
    """CloudVault application settings.

    Values are read (in order of precedence) from:
      1. real environment variables,
      2. ``backend/.env``,
      3. the repository-root ``.env``,
      4. the defaults defined here (development-safe defaults only).
    """

    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env", REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application -----------------------------------------------------
    APP_ENV: str = Field(default="development", description="development | production")
    APP_NAME: str = Field(default="CloudVault")
    DEBUG: bool = Field(default=True)

    # --- Backend server ----------------------------------------------------
    BACKEND_HOST: str = Field(default="127.0.0.1")
    BACKEND_PORT: int = Field(default=8000)

    # --- Database ----------------------------------------------------------
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://cloudvault:change_me@localhost:5432/cloudvault",
        description="SQLAlchemy URL for the PostgreSQL metadata database.",
    )

    # --- Authentication ----------------------------------------------------
    JWT_SECRET_KEY: str = Field(default="change_me", description="Secret used to sign JWTs.")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=1)

    # --- Sharing -----------------------------------------------------------
    # Base URL used when building complete share URLs returned by the API.
    # Configurable so production can point at the deployed frontend.
    PUBLIC_SHARE_BASE_URL: str = Field(
        default="http://localhost:3000",
        description="Base URL used to build public share links (frontend share page).",
    )

    # --- AWS S3 (consumed by Member 1's storage layer) ---------------------
    AWS_ACCESS_KEY_ID: str = Field(default="change_me")
    AWS_SECRET_ACCESS_KEY: str = Field(default="change_me")
    AWS_REGION: str = Field(default="ap-south-1")
    AWS_S3_BUCKET: str = Field(default="change_me")
    STORAGE_PROVIDER: str = Field(default="local")

    # --- CORS (frontend integration) ----------------------------------------
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed CORS origins.",
    )

    @field_validator("APP_ENV")
    @classmethod
    def _normalize_env(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in {"development", "production", "test"}:
            raise ValueError("APP_ENV must be one of: development, production, test")
        return value

    @field_validator("DATABASE_URL")
    @classmethod
    def _validate_database_url(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError(
                "DATABASE_URL must be a PostgreSQL URL "
                "(postgresql:// or postgresql+psycopg://)"
            )
        return value

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def validate_production_safety(self) -> None:
        """Fail clearly when production is missing real configuration.

        Development may run on placeholder defaults, but production must not
        start with an unset JWT secret: an attacker who knows the placeholder
        could forge valid tokens for any account.
        """
        if not self.is_production:
            return
        problems: list[str] = []
        if self.JWT_SECRET_KEY.strip().lower() in _UNSAFE_PLACEHOLDERS or len(self.JWT_SECRET_KEY) < 32:
            problems.append(
                "JWT_SECRET_KEY must be set to a strong random value "
                "(at least 32 characters, not a placeholder) in production."
            )
        if "change_me" in self.DATABASE_URL:
            problems.append("DATABASE_URL still contains the 'change_me' placeholder password.")
        if problems:
            raise RuntimeError(
                "Refusing to start in production with unsafe configuration:\n- "
                + "\n- ".join(problems)
            )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
