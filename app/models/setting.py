"""User-tunable settings model (non-sensitive key-value pairs)."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class Setting(Base, IDMixin, TimestampMixin):
    """
    User-specific settings stored as key-value pairs.

    Only non-sensitive settings (scrape interval, match threshold, etc.).
    Credentials are environment-only via .env.
    """

    __tablename__ = "settings"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Relationships
    user = relationship("User", back_populates="settings")
