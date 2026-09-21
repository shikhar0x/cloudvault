"""Sharing business logic: secure tokens, expiry and public lookups.

Security properties enforced here:

- Share tokens are generated with ``secrets.token_urlsafe`` (256 bits of
  entropy) — never derived from file ids, user ids, timestamps or any
  predictable value.
- Share creation always verifies file ownership against the *authenticated*
  user; a client-supplied ``user_id`` is never consulted.
- Expiry is checked server-side on every public access using timezone-aware
  UTC datetimes.
- Deleting a file cascades to its share links (database FK), so stale links
  can never expose deleted files.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import ensure_resource_owner
from app.database.base import utcnow
from app.database.models import File, ShareLink, User
from app.modules.sharing.schemas import ShareExpiry

# 256 bits of entropy, URL-safe (43 characters) — unguessable in practice.
_TOKEN_BYTES = 32
# Practically impossible, but if a token collides we retry instead of failing.
_MAX_TOKEN_ATTEMPTS = 5


class StorageNotConfiguredError(Exception):
    """Raised when the storage integration (Member 1) is not available yet."""


@dataclass(frozen=True)
class ShareDownloadInfo:
    """Everything the storage layer needs to stream a shared file.

    Returned only after the share token and its expiry have been fully
    validated. This is the integration point between sharing (Member 3)
    and object storage (Member 1).
    """

    share_id: Any
    file_id: Any
    object_key: str
    file_name: str
    mime_type: str
    file_size: int


def generate_share_token() -> str:
    """Generate a cryptographically secure, URL-safe share token."""
    return secrets.token_urlsafe(_TOKEN_BYTES)


def build_share_url(token: str) -> str:
    """Public share page URL (frontend route), based on configuration."""
    base = get_settings().PUBLIC_SHARE_BASE_URL.rstrip("/")
    return f"{base}/share/{token}"


def build_download_url(token: str) -> str:
    """Relative API URL for public download (prefix with the API base URL)."""
    return f"/api/shares/{token}/download"


def _is_token_collision(exc: IntegrityError) -> bool:
    """Whether an IntegrityError is a share-token unique violation.

    PostgreSQL SQLSTATE 23505 = unique_violation; the token's unique index
    is ``ix_share_links_token``. Unknown constraint names default to
    "collision" because that is the expected astronomically-rare case.
    """
    orig = exc.orig
    if getattr(orig, "sqlstate", None) != "23505":
        return False
    constraint = getattr(getattr(orig, "diag", None), "constraint_name", None) or ""
    return "token" in constraint.lower() or constraint == ""


def create_share(
    db: Session,
    *,
    current_user: User,
    file_id: Any,
    expires_in: ShareExpiry,
) -> ShareLink:
    """Create a share link for a file owned by ``current_user``.

    Ownership is verified against the authenticated user (403 on
    mismatch, 404 when the file does not exist). The expiry duration is
    validated by the request schema, and ``expires_at`` is computed
    server-side as a timezone-aware UTC datetime.
    """
    file = db.get(File, file_id)
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    # Rejects with 403 when the file belongs to another user.
    ensure_resource_owner(file, current_user)

    expires_at = utcnow() + timedelta(hours=expires_in.hours)

    for _ in range(_MAX_TOKEN_ATTEMPTS):
        share = ShareLink(
            file_id=file.id,
            token=generate_share_token(),
            expires_at=expires_at,
        )
        db.add(share)
        try:
            db.commit()
            db.refresh(share)
            return share
        except IntegrityError as exc:
            db.rollback()
            if _is_token_collision(exc):
                # Astronomically rare: regenerate with a fresh token.
                continue
            # e.g. the file row was deleted concurrently (FK violation).
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found.",
            ) from None
    raise HTTPException(  # pragma: no cover - astronomically unlikely
        status_code=status.HTTP_409_CONFLICT,
        detail="Could not generate a unique share token. Please retry.",
    )


def get_share_by_token(db: Session, token: str) -> ShareLink | None:
    """Look up a share link by token (unique index → efficient)."""
    if not token:
        return None
    return db.query(ShareLink).filter(ShareLink.token == token).one_or_none()


def get_active_share(db: Session, token: str) -> ShareLink:
    """Return a valid, unexpired share link or raise.

    - unknown/malformed token → ``404 Not Found``
    - expired token → ``410 Gone``
    """
    share = get_share_by_token(db, token)
    if share is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found.")
    if share.is_expired:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This share link has expired.",
        )
    return share


def get_public_share(db: Session, token: str) -> ShareLink:
    """Public lookup: valid, unexpired share whose file still exists."""
    share = get_active_share(db, token)
    # The FK cascade makes a dangling share practically impossible, but the
    # file is still checked defensively before exposing public information.
    if share.file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found.")
    return share


def get_validated_download_info(db: Session, token: str) -> ShareDownloadInfo:
    """Validate a share token for public download and return file info.

    All validation (existence + expiry) happens here, server-side; the
    storage layer can trust the returned ``object_key``.
    """
    share = get_active_share(db, token)
    file = share.file
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found.")
    return ShareDownloadInfo(
        share_id=share.id,
        file_id=file.id,
        object_key=file.object_key,
        file_name=file.file_name,
        mime_type=file.mime_type,
        file_size=file.file_size,
    )


def resolve_storage_provider() -> Any:
    """Integration point for Member 1's storage abstraction.

    Imports the storage provider factory from ``app.infrastructure.storage``
    when it has been implemented by the files/storage owner. Until then a
    :class:`StorageNotConfiguredError` is raised and the public download
    endpoint responds with ``501 Not Implemented`` instead of failing
    validation-quietly.

    Expected contract (documented in docs/api/api.md)::

        provider = resolve_storage_provider()
        stream = provider.download(object_key)   # binary stream of the object
    """
    try:
        from app.infrastructure.storage import get_storage_provider  # type: ignore
    except ImportError as exc:
        raise StorageNotConfiguredError(
            "Storage provider is not implemented yet (Member 1: "
            "app/infrastructure/storage)."
        ) from exc
    return get_storage_provider()
