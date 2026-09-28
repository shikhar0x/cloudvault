from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.models import File, Folder, User
from app.modules.storage.schemas import StorageStatsResponse

DEFAULT_QUOTA_BYTES = 10 * 1024 * 1024 * 1024  # 10 GB


def get_storage_stats(
    db: Session,
    *,
    current_user: User,
) -> StorageStatsResponse:
    used_bytes = (
        db.query(func.coalesce(func.sum(File.file_size), 0))
        .filter(File.user_id == current_user.id)
        .scalar()
    )

    file_count = (
        db.query(func.count(File.id))
        .filter(File.user_id == current_user.id)
        .scalar()
    )

    folder_count = (
        db.query(func.count(Folder.id))
        .filter(Folder.user_id == current_user.id)
        .scalar()
    )

    return StorageStatsResponse(
        used_bytes=int(used_bytes or 0),
        total_bytes=DEFAULT_QUOTA_BYTES,
        file_count=int(file_count or 0),
        folder_count=int(folder_count or 0),
    )
