from __future__ import annotations

from pydantic import BaseModel


class StorageStatsResponse(BaseModel):
    used_bytes: int
    total_bytes: int
    file_count: int
    folder_count: int
