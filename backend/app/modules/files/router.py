from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File as FastAPIFile, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.models import User
from app.database.session import get_db
from app.modules.files import service
from app.modules.files.schemas import FileResponse

router = APIRouter(
    prefix="/api/files",
    tags=["Files"],
)


@router.post(
    "/upload",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file into storage",
)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    folder_id: uuid.UUID | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    # Read file content or get size
    file_bytes = await file.read()
    file_size = len(file_bytes)
    
    # Reset stream pointer
    await file.seek(0)

    file_record = service.upload_file(
        db,
        current_user=current_user,
        file_object=file.file,
        file_name=file.filename,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        folder_id=folder_id,
    )
    return FileResponse.model_validate(file_record)


@router.get(
    "",
    response_model=list[FileResponse],
    summary="List files in the current folder",
)
def list_files(
    folder_id: uuid.UUID | None = Query(default=None, description="Folder ID to list files from"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[FileResponse]:
    files = service.list_files(db, current_user=current_user, folder_id=folder_id)
    return [FileResponse.model_validate(f) for f in files]


@router.get(
    "/{file_id}",
    response_model=FileResponse,
    summary="Get file metadata by ID",
)
def get_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    file = service.get_file(db, current_user=current_user, file_id=file_id)
    return FileResponse.model_validate(file)


@router.get(
    "/{file_id}/download",
    summary="Download a file",
)
def download_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    stream, file_record = service.download_file(db, current_user=current_user, file_id=file_id)
    return StreamingResponse(
        stream,
        media_type=file_record.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{file_record.file_name}"',
            "Content-Length": str(file_record.file_size),
        },
    )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a file from storage and database",
)
def delete_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    service.delete_file(db, current_user=current_user, file_id=file_id)
