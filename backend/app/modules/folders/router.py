from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.models import User
from app.database.session import get_db
from app.modules.folders import service
from app.modules.folders.schemas import FolderCreateRequest, FolderResponse

router = APIRouter(
    prefix="/api/folders",
    tags=["Folders"],
)


@router.post(
    "",
    response_model=FolderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new folder",
)
def create_folder(
    payload: FolderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FolderResponse:
    folder = service.create_folder(
        db,
        current_user=current_user,
        name=payload.name,
        parent_id=payload.parent_id,
    )
    return FolderResponse.model_validate(folder)


@router.get(
    "",
    response_model=list[FolderResponse],
    summary="List folders in the current directory",
)
def list_folders(
    parent_id: uuid.UUID | None = Query(default=None, description="Parent folder ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[FolderResponse]:
    folders = service.list_folders(db, current_user=current_user, parent_id=parent_id)
    return [FolderResponse.model_validate(f) for f in folders]


@router.get(
    "/{folder_id}",
    response_model=FolderResponse,
    summary="Get folder details by ID",
)
def get_folder(
    folder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FolderResponse:
    folder = service.get_folder(db, current_user=current_user, folder_id=folder_id)
    return FolderResponse.model_validate(folder)


@router.delete(
    "/{folder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a folder and its contents",
)
def delete_folder(
    folder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    service.delete_folder(db, current_user=current_user, folder_id=folder_id)
