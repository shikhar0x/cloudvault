"""User model.

Passwords are stored only as Argon2id hashes. Email addresses are always
normalized (lower-cased, trimmed) before being persisted, and a database
check constraint enforces that normalization invariant.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    folders: Mapped[list["Folder"]] = relationship(  # noqa: F821
        back_populates="owner",
        foreign_keys="Folder.user_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    files: Mapped[list["File"]] = relationship(  # noqa: F821
        back_populates="owner",
        foreign_keys="File.user_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        # The naming convention prefixes the table name automatically:
        # final constraint name is ck_users_email_lowercase.
        CheckConstraint(
            "email = lower(email)",
            name="email_lowercase",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<User id={self.id} email={self.email!r}>"
