from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.models import User
from app.database.session import get_db
from app.modules.storage import service
from app.modules.storage.schemas import StorageStatsResponse

router = APIRouter(
    prefix="/api/storage",
    tags=["Storage"],
)


@router.get(
    "/stats",
    response_model=StorageStatsResponse,
    summary="Get user's cloud storage usage statistics",
)
def get_storage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StorageStatsResponse:
    return service.get_storage_stats(db, current_user=current_user)
