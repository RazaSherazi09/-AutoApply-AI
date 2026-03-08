"""Pydantic schemas for resume endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ResumeResponse(BaseModel):
    """Resume detail returned by API."""

    id: int
    user_id: int
    file_name: str
    version: int
    parent_id: int | None = None
    structured_data: str  # JSON string
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeListResponse(BaseModel):
    """Paginated resume listing."""

    items: list[ResumeResponse]
    total: int
