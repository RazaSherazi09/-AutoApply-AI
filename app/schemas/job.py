"""Pydantic schemas for job endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class JobResponse(BaseModel):
    """Job listing returned by API."""

    id: int
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    job_type: str
    experience_level: str
    remote_status: str
    salary_min: float | None = None
    salary_max: float | None = None
    extracted_skills: str  # JSON array string
    created_at: datetime

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    """Paginated job listing."""

    items: list[JobResponse]
    total: int


class ScrapeRequest(BaseModel):
    """Manual scrape trigger request."""

    query: str = "software engineer"
    location: str = "remote"
    providers: list[str] = ["adzuna"]  # Which scrapers to run
