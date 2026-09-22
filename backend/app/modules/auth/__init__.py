"""Authentication module: registration, login, JWT-protected identity."""

from app.modules.auth import router, schemas, service

__all__ = ["router", "schemas", "service"]
