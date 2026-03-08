"""Job listing model with normalized fields and composite dedup hash."""

from __future__ import annotations

from sqlalchemy import Float, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class Job(Base, IDMixin, TimestampMixin):
    """
    Scraped job listing.

    Deduplication via ``content_hash = sha256(title + company + location)``.
    Extracted skills stored as JSON array string.
    """

    __tablename__ = "jobs"

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    company: Mapped[str] = mapped_column(String(256), nullable=False)
    location: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    content_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )  # sha256(title+company+location)
    source: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # adzuna, greenhouse, lever, workday, career_page

    # Normalized fields
    job_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="full_time"
    )  # full_time, part_time, contract, internship
    experience_level: Mapped[str] = mapped_column(
        String(32), nullable=False, default="mid"
    )  # entry, mid, senior, lead, executive
    remote_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unknown"
    )  # remote, hybrid, onsite, unknown

    # Salary (optional)
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)

    # NLP-extracted skills from job description
    extracted_skills: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )  # JSON array of skill strings

    # Float32 byte embedding
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    # Relationships
    matches = relationship("Match", back_populates="job", lazy="selectin")
