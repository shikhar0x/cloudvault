from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import ensure_resource_owner
from app.database.models import File, Folder, User
from app.infrastructure.storage import get_storage_provider


def create_folder(
    db: Session,
    *,
    current_user: User,
    name: str,
    parent_id: uuid.UUID | None = None,
) -> Folder:
    if parent_id is not None:
        parent = db.get(Folder, parent_id)
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found.",
            )
        ensure_resource_owner(parent, current_user)

    folder = Folder(
        user_id=current_user.id,
        name=name.strip(),
        parent_folder_id=parent_id,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


def list_folders(
    db: Session,
    *,
    current_user: User,
    parent_id: uuid.UUID | None = None,
) -> list[Folder]:
    query = db.query(Folder).filter(Folder.user_id == current_user.id)
    if parent_id is not None:
        query = query.filter(Folder.parent_folder_id == parent_id)
    else:
        query = query.filter(Folder.parent_folder_id.is_(None))
    return query.order_by(Folder.name.asc()).all()


def get_folder(
    db: Session,
    *,
    current_user: User,
    folder_id: uuid.UUID,
) -> Folder:
    folder = db.get(Folder, folder_id)
    if folder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found.",
        )
    ensure_resource_owner(folder, current_user)
    return folder


def delete_folder(
    db: Session,
    *,
    current_user: User,
    folder_id: uuid.UUID,
) -> None:
    folder = get_folder(db, current_user=current_user, folder_id=folder_id)
    
    # Recursively delete files from storage provider
    storage = get_storage_provider()
    
    def _delete_folder_files(target_folder_id: uuid.UUID):
        # Delete direct files
        files = db.query(File).filter(File.folder_id == target_folder_id).all()
        for f in files:
            storage.delete(f.object_key)
        
        # Recurse children
        children = db.query(Folder).filter(Folder.parent_folder_id == target_folder_id).all()
        for child in children:
            _delete_folder_files(child.id)

    _delete_folder_files(folder.id)

    db.delete(folder)
    db.commit()
