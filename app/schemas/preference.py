"""Pydantic schemas for user preferences."""

from __future__ import annotations

from pydantic import BaseModel


class PreferenceUpdate(BaseModel):
    """Request to update user preferences."""

    desired_titles: list[str] = []
    desired_locations: list[str] = []
    excluded_companies: list[str] = []
    min_salary: float | None = None
    remote_only: bool = False
    country: str = "Worldwide"
    workplace_type: str = "Any"


class PreferenceResponse(BaseModel):
    """Current user preferences."""

    id: int
    user_id: int
    desired_titles: str  # JSON array
    desired_locations: str  # JSON array
    excluded_companies: str  # JSON array
    min_salary: float | None = None
    remote_only: bool
    country: str
    workplace_type: str

    model_config = {"from_attributes": True}
