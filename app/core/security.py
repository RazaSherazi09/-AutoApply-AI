"""
JWT-based authentication and password hashing utilities.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# ── Password hashing ──
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _truncate_password(plain: str) -> str:
    """Truncate password to 72 bytes (bcrypt limit)."""
    return plain.encode("utf-8")[:72].decode("utf-8", errors="ignore")


def hash_password(plain: str) -> str:
    """Return bcrypt hash of *plain* password (truncated to 72 bytes)."""
    return pwd_context.hash(_truncate_password(plain))


def verify_password(plain: str, hashed: str) -> bool:
    """Verify *plain* password against *hashed* value."""
    return pwd_context.verify(_truncate_password(plain), hashed)


# ── JWT tokens ──

def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Claims to embed (must include ``sub`` with user ID/email).
        expires_delta: Custom expiry; falls back to config default.

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expiry_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT token.

    Raises:
        JWTError: If token is invalid or expired.

    Returns:
        Decoded claims dictionary.
    """
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
