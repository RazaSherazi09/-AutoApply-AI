"""
Application tracking routes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.application import Application
from app.models.match import Match
from app.models.resume import Resume
from app.models.user import User
from app.schemas.application import ApplicationListResponse, ApplicationResponse

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("/", response_model=ApplicationListResponse)
async def list_applications(
    skip: int = 0,
    limit: int = 50,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """List applications for the current user."""
    resume_result = await db.execute(
        select(Resume.id).where(Resume.user_id == user.id)
    )
    resume_ids = [r[0] for r in resume_result.all()]

    if not resume_ids:
        return {"items": [], "total": 0}

    # Get match IDs for user's resumes
    match_result = await db.execute(
        select(Match.id).where(Match.resume_id.in_(resume_ids))
    )
    match_ids = [r[0] for r in match_result.all()]

    if not match_ids:
        return {"items": [], "total": 0}

    query = select(Application).where(Application.match_id.in_(match_ids))
    if status_filter:
        query = query.where(Application.status == status_filter)
    query = query.order_by(Application.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    items = list(result.scalars().all())

    count_q = select(func.count(Application.id)).where(Application.match_id.in_(match_ids))
    if status_filter:
        count_q = count_q.where(Application.status == status_filter)
    total = (await db.execute(count_q)).scalar() or 0

    return {"items": items, "total": total}


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Application:
    """Get a specific application by ID."""
    resume_result = await db.execute(
        select(Resume.id).where(Resume.user_id == user.id)
    )
    resume_ids = [r[0] for r in resume_result.all()]

    match_result = await db.execute(
        select(Match.id).where(Match.resume_id.in_(resume_ids))
    )
    match_ids = [r[0] for r in match_result.all()]

    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.match_id.in_(match_ids),
        )
    )
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    return app


@router.post("/{application_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_application(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Manually retry a failed application."""
    resume_result = await db.execute(
        select(Resume.id).where(Resume.user_id == user.id)
    )
    resume_ids = [r[0] for r in resume_result.all()]

    match_result = await db.execute(
        select(Match.id).where(Match.resume_id.in_(resume_ids))
    )
    match_ids = [r[0] for r in match_result.all()]

    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.match_id.in_(match_ids),
        )
    )
    app = result.scalar_one_or_none()

    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if app.status not in ("FAILED", "MANUAL_REVIEW"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry application with status {app.status}",
        )

    # Reset for retry
    app.retry_count = 0
    app.next_retry_at = None
    app.status = "PENDING"
    app.error_log = None
    await db.flush()

    return {"message": f"Application #{application_id} queued for retry"}
