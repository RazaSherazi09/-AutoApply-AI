"""Scraper execution monitoring model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin


class ScraperRun(Base, IDMixin):
    """
    Tracks each scraper execution for monitoring and health dashboards.
    """

    __tablename__ = "scraper_runs"

    provider: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # adzuna, greenhouse, lever, workday, career_page
    status: Mapped[str] = mapped_column(
        String(16), nullable=False
    )  # SUCCESS, FAILED, PARTIAL

    jobs_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    jobs_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
