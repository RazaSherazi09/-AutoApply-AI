"""
SQLAlchemy declarative base and common column mixins.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all models."""
    pass


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class IDMixin:
    """Auto-incrementing integer primary key."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
