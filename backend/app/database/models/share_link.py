"""Share link model.

A share link grants public, time-limited access to a single file through a
cryptographically secure random token. The unique index on ``token`` makes
token lookups efficient and guarantees uniqueness at the database level.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, utcnow


def as_aware_utc(value: datetime) -> datetime:
    """Return ``value`` as a timezone-aware UTC datetime (defensive helper).

    PostgreSQL returns aware datetimes for ``TIMESTAMPTZ`` columns; this
    guard keeps comparisons correct even if a naive value sneaks in.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class ShareLink(Base, TimestampMixin):
    __tablename__ = "share_links"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    file: Mapped["File"] = relationship(  # noqa: F821
        back_populates="share_links",
        foreign_keys=[file_id],
    )

    @property
    def is_expired(self) -> bool:
        """Whether the link has expired (server-side, timezone-aware)."""
        return as_aware_utc(self.expires_at) < utcnow()

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<ShareLink id={self.id} token={self.token!r}>"
