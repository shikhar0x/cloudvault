from __future__ import annotations

import uuid
from typing import BinaryIO

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import ensure_resource_owner
from app.database.models import File, Folder, User
from app.infrastructure.storage import get_storage_provider


def upload_file(
    db: Session,
    *,
    current_user: User,
    file_object: BinaryIO,
    file_name: str,
    file_size: int,
    mime_type: str,
    folder_id: uuid.UUID | None = None,
) -> File:
    if folder_id is not None:
        folder = db.get(Folder, folder_id)
        if folder is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target folder not found.",
            )
        ensure_resource_owner(folder, current_user)

    clean_name = file_name.strip()
    object_key = f"{current_user.id}/{uuid.uuid4()}_{clean_name}"

    storage = get_storage_provider()
    storage.upload(file_object, object_key, content_type=mime_type)

    file_record = File(
        user_id=current_user.id,
        folder_id=folder_id,
        file_name=clean_name,
        object_key=object_key,
        file_size=file_size,
        mime_type=mime_type or "application/octet-stream",
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    return file_record


def list_files(
    db: Session,
    *,
    current_user: User,
    folder_id: uuid.UUID | None = None,
) -> list[File]:
    query = db.query(File).filter(File.user_id == current_user.id)
    if folder_id is not None:
        query = query.filter(File.folder_id == folder_id)
    else:
        query = query.filter(File.folder_id.is_(None))
    return query.order_by(File.created_at.desc()).all()


def get_file(
    db: Session,
    *,
    current_user: User,
    file_id: uuid.UUID,
) -> File:
    file = db.get(File, file_id)
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found.",
        )
    ensure_resource_owner(file, current_user)
    return file


def download_file(
    db: Session,
    *,
    current_user: User,
    file_id: uuid.UUID,
):
    file = get_file(db, current_user=current_user, file_id=file_id)
    storage = get_storage_provider()
    stream = storage.download(file.object_key)
    return stream, file


def delete_file(
    db: Session,
    *,
    current_user: User,
    file_id: uuid.UUID,
) -> None:
    file = get_file(db, current_user=current_user, file_id=file_id)
    storage = get_storage_provider()
    storage.delete(file.object_key)
    db.delete(file)
    db.commit()
