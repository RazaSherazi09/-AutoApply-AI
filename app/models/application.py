"""Application model with retry tracking and handler type."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class Application(Base, IDMixin, TimestampMixin):
    """
    Record of an application attempt for an approved match.

    Tracks handler used, retry count, and scheduled next retry.
    """

    __tablename__ = "applications"

    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id"), unique=True, nullable=False, index=True
    )

    # How we're applying
    method: Mapped[str] = mapped_column(
        String(16), nullable=False
    )  # EMAIL, WEB
    handler_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="GENERIC"
    )  # EMAIL, LINKEDIN, GREENHOUSE, LEVER, WORKDAY, GENERIC

    # Status workflow
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING"
    )  # PENDING, SENT, SUBMITTED, FAILED, MANUAL_REVIEW

    # Retry mechanism
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Tracking
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    match = relationship("Match", back_populates="application")
