"""
FastAPI dependency injection: DB session, current user.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate JWT and return the current authenticated user.

    Raises:
        HTTPException 401: If token is invalid or user not found.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_email: str | None = payload.get("sub")
        if user_email is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    result = await db.execute(select(User).where(User.email == user_email))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exc

    return user
