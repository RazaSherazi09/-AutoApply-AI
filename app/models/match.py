"""Match model storing hybrid score breakdown."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class Match(Base, IDMixin, TimestampMixin):
    """
    A scored match between a resume and a job.

    All sub-scores are normalized to [0, 1] before weighting.
    ``final_score = 0.6*semantic + 0.2*skill + 0.1*title + 0.1*location``
    """

    __tablename__ = "matches"

    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False, index=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), nullable=False, index=True)

    # Hybrid score breakdown (all [0, 1])
    semantic_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    skill_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    title_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    location_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    final_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Status workflow
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING_APPROVAL"
    )  # PENDING_APPROVAL, APPROVED, REJECTED

    # Relationships
    job = relationship("Job", back_populates="matches")
    resume = relationship("Resume", back_populates="matches")
    application = relationship("Application", back_populates="match", uselist=False, lazy="selectin")
