"""
Match routes: list, approve, reject.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.job import Job
from app.models.match import Match
from app.models.resume import Resume
from app.models.user import User
from app.schemas.match import MatchActionResponse, MatchListResponse, MatchResponse

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("/", response_model=MatchListResponse)
async def list_matches(
    skip: int = 0,
    limit: int = 50,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """List matches for the current user's resumes."""
    # Get user's resume IDs
    resume_result = await db.execute(
        select(Resume.id).where(Resume.user_id == user.id)
    )
    resume_ids = [r[0] for r in resume_result.all()]

    if not resume_ids:
        return {"items": [], "total": 0}

    query = select(Match).where(Match.resume_id.in_(resume_ids))
    if status_filter:
        query = query.where(Match.status == status_filter)
    query = query.order_by(Match.final_score.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    matches = list(result.scalars().all())

    # Enrich with job info
    items: list[dict] = []
    for m in matches:
        job_result = await db.execute(select(Job).where(Job.id == m.job_id))
        job = job_result.scalar_one_or_none()

        item = MatchResponse(
            id=m.id,
            job_id=m.job_id,
            resume_id=m.resume_id,
            semantic_score=m.semantic_score,
            skill_score=m.skill_score,
            title_score=m.title_score,
            location_score=m.location_score,
            final_score=m.final_score,
            status=m.status,
            created_at=m.created_at,
            job_title=job.title if job else None,
            job_company=job.company if job else None,
            job_url=job.url if job else None,
        )
        items.append(item)

    # Total count
    count_q = select(func.count(Match.id)).where(Match.resume_id.in_(resume_ids))
    if status_filter:
        count_q = count_q.where(Match.status == status_filter)
    total = (await db.execute(count_q)).scalar() or 0

    return {"items": items, "total": total}


@router.post("/{match_id}/approve", response_model=MatchActionResponse)
async def approve_match(
    match_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Approve a pending match for auto-apply."""
    match = await _get_user_match(db, match_id, user)

    if match.status != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Match is already {match.status}",
        )

    match.status = "APPROVED"
    await db.flush()
    return {"id": match.id, "status": "APPROVED", "message": "Match approved for application"}


@router.post("/{match_id}/reject", response_model=MatchActionResponse)
async def reject_match(
    match_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Reject a pending match."""
    match = await _get_user_match(db, match_id, user)

    if match.status != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Match is already {match.status}",
        )

    match.status = "REJECTED"
    await db.flush()
    return {"id": match.id, "status": "REJECTED", "message": "Match rejected"}


async def _get_user_match(
    db: AsyncSession, match_id: int, user: User
) -> Match:
    """Fetch a match ensuring it belongs to the current user."""
    resume_result = await db.execute(
        select(Resume.id).where(Resume.user_id == user.id)
    )
    resume_ids = [r[0] for r in resume_result.all()]

    result = await db.execute(
        select(Match).where(Match.id == match_id, Match.resume_id.in_(resume_ids))
    )
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    return match
