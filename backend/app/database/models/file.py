"""File metadata model.

The database stores *metadata only* — binary file content lives in object
storage (AWS S3) and is referenced by ``object_key``. This model is shared
with Member 1's files module.
"""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class File(Base, TimestampMixin):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Root-level files have no folder. Deleting a folder deletes the metadata
    # of the files it contains (the storage layer must remove S3 objects
    # first — see docs/database/database-design.md).
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    object_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)

    owner: Mapped["User"] = relationship(  # noqa: F821
        back_populates="files",
        foreign_keys=[user_id],
    )
    folder: Mapped["Folder | None"] = relationship(  # noqa: F821
        back_populates="files",
        foreign_keys=[folder_id],
    )
    share_links: Mapped[list["ShareLink"]] = relationship(  # noqa: F821
        back_populates="file",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        # Final constraint name (via naming convention): ck_files_file_size_non_negative.
        CheckConstraint("file_size >= 0", name="file_size_non_negative"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<File id={self.id} file_name={self.file_name!r}>"
