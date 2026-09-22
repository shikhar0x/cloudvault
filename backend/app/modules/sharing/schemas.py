"""Pydantic schemas for the sharing module."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ShareExpiry(str, Enum):
    """Allowed link lifetimes for the mini project.

    ``value`` is the human-readable duration; ``hours`` is what the
    service uses to compute ``expires_at``.
    """

    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    SEVEN_DAYS = "7d"

    @property
    def hours(self) -> int:
        return {"1h": 1, "1d": 24, "7d": 168}[self.value]


class ShareCreateRequest(BaseModel):
    file_id: uuid.UUID
    expires_in: ShareExpiry = Field(
        default=ShareExpiry.ONE_DAY,
        description="Link lifetime: '1h', '1d' or '7d'.",
    )


class SharedFileInfo(BaseModel):
    """Safe file information exposed through public share endpoints."""

    id: uuid.UUID
    file_name: str
    mime_type: str
    file_size: int


class ShareResponse(BaseModel):
    """Response for the owner after creating a share link."""

    id: uuid.UUID
    token: str
    share_url: str
    expires_at: datetime
    created_at: datetime
    file: SharedFileInfo

    model_config = ConfigDict(from_attributes=True)


class PublicShareResponse(BaseModel):
    """Public response for ``GET /api/shares/{token}``.

    Contains only safe public file information plus the expiry — never
    owner details or internal database fields.
    """

    file: SharedFileInfo
    expires_at: datetime
    download_url: str
