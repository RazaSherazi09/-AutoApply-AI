"""Pydantic schemas for authentication endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Registration request payload."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=256)


class UserLogin(BaseModel):
    """Login request payload."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user information."""

    id: int
    email: str
    full_name: str
    is_active: bool

    model_config = {"from_attributes": True}
