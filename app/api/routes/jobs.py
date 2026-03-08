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
    """List scraped jobs with optional filters (isolated to user)."""
    query = select(Job).where(Job.user_id == user.id)

    if source:
        query = query.where(Job.source == source)
    if search:
        query = query.where(Job.title.ilike(f"%{search}%"))
    if remote_only:
        query = query.where(Job.remote_status == "remote")

    query = query.order_by(Job.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = list(result.scalars().all())

    # Total count for user
    count_q = select(func.count(Job.id)).where(Job.user_id == user.id)
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
    """Trigger a smart scrape run (async background task) using user profile."""
    background_tasks.add_task(_run_scrape, user.id)
    return {"message": "Smart contextual scrape started"}


async def _run_scrape(user_id: int) -> None:
    """Background task to run scrapers using dynamic profile context."""
    from app.core.database import async_session_factory
    from app.services.scraper_service import ScraperService
    from app.models.preference import Preference
    from app.models.resume import Resume
    import json

    svc = ScraperService()
    async with async_session_factory() as db:
        try:
            # 1. Fetch User Preferences
            pref_result = await db.execute(select(Preference).where(Preference.user_id == user_id))
            pref = pref_result.scalar_one_or_none()

            # 2. Fetch User Resume
            res_result = await db.execute(
                select(Resume).where(Resume.user_id == user_id).order_by(Resume.version.desc()).limit(1)
            )
            resume = res_result.scalar_one_or_none()

            # 3. Construct Query
            search_query = "Software Engineer"
            target_location = "Remote"
            
            if pref:
                # Compile desired titles
                titles = []
                try: 
                    titles = json.loads(pref.desired_titles)
                except:
                    pass
                
                # Expand with resume skills if short on titles
                if not titles and resume and resume.structured_data:
                    try:
                        rdata = json.loads(resume.structured_data)
                        if rdata.get("skills"):
                           titles = [f"{rdata['skills'][0]} Developer"] 
                    except:
                        pass
                
                if titles:
                    search_query = " ".join(titles)

                # Compile location
                locs = []
                try:
                    locs = json.loads(pref.desired_locations)
                except:
                    pass
                
                if pref.country and pref.country != "Worldwide":
                    locs.append(pref.country)
                    
                if locs:
                    target_location = ", ".join(locs)
                    
                if pref.workplace_type and pref.workplace_type != "Any":
                    target_location = f"{pref.workplace_type} {target_location}".strip()
                    
                if pref.remote_only:
                    target_location = "Remote"

            from loguru import logger
            logger.info("Starting smart scrape for User {} | Query: [{}] | Location: [{}]", user_id, search_query, target_location)

            runs = await svc.scrape_all(db, user_id=user_id, query=search_query, location=target_location)
            await db.commit()
        except Exception:
            await db.rollback()
            from loguru import logger
            logger.exception("Background smart scrape failed for User {}", user_id)


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
