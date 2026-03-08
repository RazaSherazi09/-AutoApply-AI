"""Pydantic schemas for match endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MatchResponse(BaseModel):
    """Match detail with full hybrid score breakdown."""

    id: int
    job_id: int
    resume_id: int
    semantic_score: float
    skill_score: float
    title_score: float
    location_score: float
    final_score: float
    status: str
    created_at: datetime

    # Inline job info for convenience
    job_title: str | None = None
    job_company: str | None = None
    job_url: str | None = None

    model_config = {"from_attributes": True}


class MatchListResponse(BaseModel):
    """Paginated match listing."""

    items: list[MatchResponse]
    total: int


class MatchActionResponse(BaseModel):
    """Response after approve/reject action."""

    id: int
    status: str
    message: str
