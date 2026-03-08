"""
Settings & preferences routes (non-sensitive only).
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.preference import Preference
from app.models.setting import Setting
from app.models.user import User
from app.schemas.preference import PreferenceResponse, PreferenceUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ── Preferences ──

@router.get("/preferences", response_model=PreferenceResponse)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Preference:
    """Get current user's job search preferences."""
    result = await db.execute(
        select(Preference).where(Preference.user_id == user.id)
    )
    pref = result.scalar_one_or_none()

    if not pref:
        # Create default preferences
        pref = Preference(user_id=user.id)
        db.add(pref)
        await db.flush()
        await db.refresh(pref)

    return pref


@router.put("/preferences", response_model=PreferenceResponse)
async def update_preferences(
    payload: PreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Preference:
    """Update user's job search preferences."""
    result = await db.execute(
        select(Preference).where(Preference.user_id == user.id)
    )
    pref = result.scalar_one_or_none()

    if not pref:
        pref = Preference(user_id=user.id)
        db.add(pref)

    pref.desired_titles = json.dumps(payload.desired_titles)
    pref.desired_locations = json.dumps(payload.desired_locations)
    pref.excluded_companies = json.dumps(payload.excluded_companies)
    pref.min_salary = payload.min_salary
    pref.remote_only = payload.remote_only
    pref.country = payload.country
    pref.workplace_type = payload.workplace_type

    await db.flush()
    await db.refresh(pref)
    return pref


# ── User settings (non-sensitive key-value) ──

# Allowed setting keys (no credentials)
ALLOWED_SETTINGS = {
    "scrape_interval_minutes",
    "match_threshold",
    "max_applications_per_day",
    "required_keywords",
}


@router.get("/config")
async def get_settings_kv(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Get user's non-sensitive settings."""
    result = await db.execute(
        select(Setting).where(Setting.user_id == user.id)
    )
    settings = result.scalars().all()
    return {s.key: s.value for s in settings}


@router.put("/config")
async def update_settings_kv(
    updates: dict[str, str],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Update user's non-sensitive settings. Only allowed keys accepted."""
    rejected = set(updates.keys()) - ALLOWED_SETTINGS
    if rejected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Settings not allowed (security): {rejected}",
        )

    for key, value in updates.items():
        result = await db.execute(
            select(Setting).where(Setting.user_id == user.id, Setting.key == key)
        )
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = value
        else:
            db.add(Setting(user_id=user.id, key=key, value=value))

    await db.flush()
    return updates
