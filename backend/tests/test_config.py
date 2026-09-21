"""Tests for application configuration (core/config.py)."""

from __future__ import annotations

import pytest

from app.core.config import Settings


class TestSettings:
    def test_development_defaults_load(self):
        settings = Settings(APP_ENV="development", DATABASE_URL="postgresql+psycopg://u:p@localhost:5432/db")
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES >= 1
        assert settings.is_production is False

    def test_env_var_precedence(self):
        """Real environment variables win over .env-file values."""
        import os

        os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "123"
        try:
            settings = Settings(APP_ENV="development", _env_file=None)
            assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 123
        finally:
            del os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"]

    def test_invalid_app_env_rejected(self):
        with pytest.raises(Exception):
            Settings(APP_ENV="staging", DATABASE_URL="postgresql+psycopg://u:p@localhost:5432/db")

    def test_non_postgres_database_url_rejected(self):
        with pytest.raises(Exception):
            Settings(APP_ENV="development", DATABASE_URL="sqlite:///dev.db")

    def test_cors_origins_parsed(self):
        settings = Settings(
            APP_ENV="development",
            DATABASE_URL="postgresql+psycopg://u:p@localhost:5432/db",
            CORS_ORIGINS="http://localhost:3000, https://cloudvault.example.com ,,",
        )
        assert settings.cors_origins_list == [
            "http://localhost:3000",
            "https://cloudvault.example.com",
        ]


class TestProductionSafety:
    def _production_settings(self, **overrides) -> Settings:
        values = dict(
            APP_ENV="production",
            DATABASE_URL="postgresql+psycopg://cloudvault:realpassword@db:5432/cloudvault",
            JWT_SECRET_KEY="x" * 48,
        )
        values.update(overrides)
        return Settings(**values)

    def test_placeholder_jwt_secret_rejected_in_production(self):
        settings = self._production_settings(JWT_SECRET_KEY="change_me")
        with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
            settings.validate_production_safety()

    def test_short_jwt_secret_rejected_in_production(self):
        settings = self._production_settings(JWT_SECRET_KEY="too-short-secret")
        with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
            settings.validate_production_safety()

    def test_placeholder_database_password_rejected_in_production(self):
        settings = self._production_settings(
            DATABASE_URL="postgresql+psycopg://cloudvault:change_me@db:5432/cloudvault"
        )
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            settings.validate_production_safety()

    def test_valid_production_config_passes(self):
        settings = self._production_settings()
        settings.validate_production_safety()  # must not raise

    def test_development_allows_placeholders(self):
        settings = Settings(
            APP_ENV="development",
            DATABASE_URL="postgresql+psycopg://cloudvault:change_me@localhost:5432/cloudvault",
            JWT_SECRET_KEY="change_me",
        )
        settings.validate_production_safety()  # must not raise in development
