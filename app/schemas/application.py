"""Pydantic schemas for application endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ApplicationResponse(BaseModel):
    """Application detail with retry tracking."""

    id: int
    match_id: int
    method: str
    handler_type: str
    status: str
    retry_count: int
    max_retries: int
    next_retry_at: datetime | None = None
    applied_at: datetime | None = None
    error_log: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationListResponse(BaseModel):
    """Paginated application listing."""

    items: list[ApplicationResponse]
    total: int
