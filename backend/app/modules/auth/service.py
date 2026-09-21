"""Authentication business logic.

Responsibilities: registration, credential verification and user lookup.
The service is the only place that touches ``password_hash``; routers and
schemas never see it.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, dummy_verify, hash_password, verify_password
from app.database.models import User


def get_user_by_email(db: Session, email: str) -> User | None:
    """Find a user by email (email is stored normalized/lowercase)."""
    return db.query(User).filter(User.email == email.strip().lower()).one_or_none()


def get_user_by_id(db: Session, user_id) -> User | None:
    """Find a user by primary key."""
    return db.get(User, user_id)


def register_user(db: Session, *, name: str, email: str, password: str) -> User:
    """Register a new user.

    Steps: validate input (done by the schema), normalize email, check for
    an existing account, hash the password, persist. Duplicate emails are
    reported as a clear 409; a rare concurrent-registration race is caught
    by the database unique constraint and mapped to the same error.
    """
    existing = get_user_by_email(db, email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Concurrent registration with the same email slipped past the
        # pre-check; report the same client-facing error.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from None
    db.refresh(user)
    return user


def authenticate_user(db: Session, *, email: str, password: str) -> User:
    """Verify credentials and return the user, or raise 401.

    The same generic error message — and roughly the same amount of work —
    is used for unknown emails and wrong passwords so that attackers
    cannot distinguish the two cases.
    """
    _invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
    )
    user = get_user_by_email(db, email)
    if user is None:
        # Equalize timing with a real password verification.
        dummy_verify()
        raise _invalid
    if not verify_password(password, user.password_hash):
        raise _invalid
    return user


def login_user(db: Session, *, email: str, password: str) -> tuple[User, str]:
    """Authenticate a user and issue a signed JWT for them."""
    user = authenticate_user(db, email=email, password=password)
    token = create_access_token(subject=user.id)
    return user, token
