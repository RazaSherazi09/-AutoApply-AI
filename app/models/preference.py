"""User job preferences model."""

from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class Preference(Base, IDMixin, TimestampMixin):
    """
    User's desired job search criteria.

    List fields (desired_titles, etc.) stored as JSON arrays.
    One-to-one with User.
    """

    __tablename__ = "preferences"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False, index=True
    )

    # Search criteria (JSON arrays)
    desired_titles: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )  # ["Software Engineer", "Backend Developer"]
    desired_locations: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )  # ["San Francisco", "Remote"]
    excluded_companies: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )  # ["CompanyX"]

    min_salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    remote_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="preferences")
