from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FolderCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Folder name")
    parent_id: uuid.UUID | None = Field(default=None, description="Parent folder ID if nested")


class FolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    parent_folder_id: uuid.UUID | None = None
    created_at: datetime
