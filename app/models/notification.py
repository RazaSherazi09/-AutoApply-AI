"""Notification model with deduplication hash."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class Notification(Base, IDMixin, TimestampMixin):
    """
    Tracks sent notifications to prevent duplicates.

    ``content_hash = sha256(user_id + type + reference_id)`` ensures
    each notification is only sent once.
    """

    __tablename__ = "notifications"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # NEW_MATCH, APPLICATION_STATUS, SCRAPER_COMPLETE
    reference_id: Mapped[str] = mapped_column(
        String(128), nullable=False
    )  # ID of the related entity
    channel: Mapped[str] = mapped_column(
        String(16), nullable=False, default="EMAIL"
    )  # EMAIL, DASHBOARD

    content_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )  # sha256 dedup key

    message: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Relationships
    user = relationship("User", back_populates="notifications")
