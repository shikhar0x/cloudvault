"""Folder model with nesting support.

Folders can be nested through ``parent_folder_id``. A *composite* foreign key
on ``(user_id, parent_folder_id)`` guarantees at the database level that a
folder can never reference a parent folder belonging to a different user,
in addition to service-level validation.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Folder(Base, TimestampMixin):
    __tablename__ = "folders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_folder_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    owner: Mapped["User"] = relationship(  # noqa: F821
        back_populates="folders",
        foreign_keys=[user_id],
    )
    parent: Mapped["Folder | None"] = relationship(
        back_populates="children",
        remote_side="Folder.id",
        foreign_keys=[parent_folder_id],
    )
    children: Mapped[list["Folder"]] = relationship(
        back_populates="parent",
        foreign_keys=[parent_folder_id],
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    files: Mapped[list["File"]] = relationship(  # noqa: F821
        back_populates="folder",
        foreign_keys="File.folder_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        # Target of the composite foreign key below.
        UniqueConstraint("user_id", "id", name="uq_folders_user_id_id"),
        # A parent folder must belong to the same user as the child folder.
        ForeignKeyConstraint(
            ["user_id", "parent_folder_id"],
            ["folders.user_id", "folders.id"],
            ondelete="CASCADE",
            name="fk_folders_user_id_parent_folder_id_folders",
        ),
        # A folder can never be its own parent.
        CheckConstraint(
            "parent_folder_id IS NULL OR parent_folder_id <> id",
            name="no_self_parent",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Folder id={self.id} name={self.name!r}>"
