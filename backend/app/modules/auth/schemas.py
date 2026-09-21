"""Pydantic schemas for the authentication module.

Response schemas never expose ``password`` or ``password_hash`` — the
serialization surface is exactly what the API contract documents.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Simple, dependency-free email validation. Normalization (trim + lowercase)
# happens in the same validator so a canonical form is always stored.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: str) -> str:
    """Validate and normalize an email address (trim + lowercase)."""
    normalized = value.strip().lower()
    if not _EMAIL_RE.match(normalized):
        raise ValueError("Invalid email address")
    return normalized


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(max_length=320)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name must not be empty")
        return value

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return normalize_email(value)


class LoginRequest(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return normalize_email(value)


class UserResponse(BaseModel):
    """Safe public representation of a user."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
