from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_name: str
    folder_id: uuid.UUID | None = None
    file_size: int
    mime_type: str
    object_key: str
    created_at: datetime
