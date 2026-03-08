"""User account model."""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class User(Base, IDMixin, TimestampMixin):
    """Registered user who uploads resumes and approves applications."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    resumes = relationship("Resume", back_populates="user", lazy="selectin")
    preferences = relationship("Preference", back_populates="user", lazy="selectin", uselist=False)
    notifications = relationship("Notification", back_populates="user", lazy="selectin")
    settings = relationship("Setting", back_populates="user", lazy="selectin")
