"""Authentication API routes.

Routes stay thin: validation happens in schemas, business rules in the
service, persistence through the database session dependency.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.models import User
from app.database.session import get_db
from app.modules.auth import service
from app.modules.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    """Create an account with name, email and password.

    The password is hashed with Argon2id before persistence; the response
    contains only safe user fields. A duplicate email returns ``409``.
    """
    return service.register_user(
        db, name=payload.name, email=payload.email, password=payload.password
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and receive an access token",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Verify credentials and return a signed JWT.

    Invalid credentials return ``401`` with a generic message that does
    not reveal whether the email exists.
    """
    user, token = service.login_user(db, email=payload.email, password=payload.password)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
)
def me(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's own profile.

    Requires a valid ``Authorization: Bearer <token>`` header; this is the
    canonical protected-endpoint check used by the frontend.
    """
    return current_user
