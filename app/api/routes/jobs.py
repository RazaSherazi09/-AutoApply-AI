"""
Job listing routes: list, filter, trigger manual scrape.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.job import Job
from app.models.scraper_run import ScraperRun
from app.models.user import User
from app.schemas.job import JobListResponse, JobResponse, ScrapeRequest

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    skip: int = 0,
    limit: int = 50,
    source: str | None = None,
    search: str | None = None,
    remote_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """List scraped jobs with optional filters."""
    query = select(Job)

    if source:
        query = query.where(Job.source == source)
    if search:
        query = query.where(Job.title.ilike(f"%{search}%"))
    if remote_only:
        query = query.where(Job.remote_status == "remote")

    query = query.order_by(Job.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = list(result.scalars().all())

    # Total count
    count_q = select(func.count(Job.id))
    if source:
        count_q = count_q.where(Job.source == source)
    if search:
        count_q = count_q.where(Job.title.ilike(f"%{search}%"))
    if remote_only:
        count_q = count_q.where(Job.remote_status == "remote")
    total = (await db.execute(count_q)).scalar() or 0

    return {"items": items, "total": total}


@router.post("/scrape", status_code=status.HTTP_202_ACCEPTED)
async def trigger_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
) -> dict:
    """Trigger a manual scrape run (async background task)."""
    background_tasks.add_task(_run_scrape, request.query, request.location)
    return {"message": "Scrape started", "query": request.query, "location": request.location}


async def _run_scrape(query: str, location: str) -> None:
    """Background task to run scrapers."""
    from app.core.database import async_session_factory
    from app.services.scraper_service import ScraperService

    svc = ScraperService()
    async with async_session_factory() as db:
        try:
            runs = await svc.scrape_all(db, query=query, location=location)
            await db.commit()
        except Exception:
            await db.rollback()
            from loguru import logger
            logger.exception("Background scrape failed")


@router.get("/scraper-runs")
async def list_scraper_runs(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict]:
    """Get recent scraper run history for monitoring."""
    result = await db.execute(
        select(ScraperRun).order_by(ScraperRun.started_at.desc()).limit(limit)
    )
    runs = result.scalars().all()
    return [
        {
            "id": r.id,
            "provider": r.provider,
            "status": r.status,
            "jobs_found": r.jobs_found,
            "jobs_new": r.jobs_new,
            "duration_seconds": r.duration_seconds,
            "error_log": r.error_log,
            "started_at": r.started_at.isoformat() if r.started_at else None,
        }
        for r in runs
    ]
