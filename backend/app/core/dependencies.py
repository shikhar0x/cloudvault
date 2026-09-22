"""Reusable FastAPI dependencies for authentication and authorization.

These are the integration points other modules (files, folders, storage)
use to protect their routes:

    current_user: User = Depends(get_current_user)

Identity always comes from the validated JWT in the ``Authorization``
header — never from a user id supplied in the request body or by the
frontend. Ownership checks go through :func:`ensure_resource_owner`.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import (
    ExpiredTokenError,
    InvalidTokenError,
    decode_access_token,
)
from app.database.models import User
from app.database.session import get_db


_bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the Bearer token."""

    if credentials is None:
        raise _unauthorized(
            "Not authenticated. Provide 'Authorization: Bearer <token>'."
        )

    if credentials.scheme.lower() != "bearer":
        raise _unauthorized(
            "Invalid authorization scheme. Use 'Bearer <token>'."
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except ExpiredTokenError:
        raise _unauthorized(
            "Token has expired. Please log in again."
        ) from None
    except InvalidTokenError:
        raise _unauthorized(
            "Invalid authentication token."
        ) from None

    user = _load_user_from_subject(db, payload["sub"])

    if user is None:
        raise _unauthorized("User no longer exists.")

    return user


def _load_user_from_subject(
    db: Session,
    subject: Any,
) -> User | None:
    """Load a user by the JWT ``sub`` claim."""

    try:
        user_id = UUID(str(subject))
    except (ValueError, AttributeError):
        return None

    return db.get(User, user_id)


def ensure_resource_owner(resource: Any, user: User) -> Any:
    """Ensure that a database resource belongs to the authenticated user."""

    owner_id = getattr(resource, "user_id", None)

    if owner_id is None or owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )

    return resource
