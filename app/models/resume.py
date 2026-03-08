"""Resume model with versioning and float32 embedding storage."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class Resume(Base, IDMixin, TimestampMixin):
    """
    Parsed resume document.

    Supports versioning: new uploads create version N+1 with ``parent_id``
    pointing to the previous version.  Embeddings stored as float32 bytes.
    """

    __tablename__ = "resumes"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_name: Mapped[str] = mapped_column(String(256), nullable=False)

    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id"), nullable=True)

    # Extracted content
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    structured_data: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}"
    )  # JSON: {name, email, phone, skills[], experience_years}

    # Float32 byte embedding (sentence-transformers)
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    # Relationships
    user = relationship("User", back_populates="resumes")
    parent = relationship("Resume", remote_side="Resume.id", lazy="selectin")
    matches = relationship("Match", back_populates="resume", lazy="selectin")
