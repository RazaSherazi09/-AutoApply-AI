"""
APScheduler-based background task scheduler.

Runs a sequential pipeline: scrape → match → notify.
Also runs independent jobs for processing applications and retries.
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.core.config import get_settings

_scheduler: AsyncIOScheduler | None = None


async def pipeline_job() -> None:
    """
    Sequential scrape → match → notify pipeline.

    Runs on the configured interval. Only proceeds to matching if new
    jobs were found, and only notifies if new matches were created.
    """
    from app.core.database import async_session_factory
    from app.services.scraper_service import ScraperService
    from app.services.matcher import MatcherService
    from app.services.notification import NotificationService
    from app.models.user import User
    from sqlalchemy import select

    logger.info("Pipeline job starting...")

    async with async_session_factory() as db:
        try:
            # Step 1: Scrape
            scraper_svc = ScraperService()
            runs = await scraper_svc.scrape_all(db)
            total_new = sum(r.jobs_new for r in runs)
            logger.info("Pipeline: scraped {} new jobs", total_new)

            # Step 2: Match (only if new jobs)
            if total_new > 0:
                matcher_svc = MatcherService()
                new_matches = await matcher_svc.match_all_pending(db)
                logger.info("Pipeline: created {} new matches", len(new_matches))

                # Step 3: Notify (only if new matches)
                if new_matches:
                    notif_svc = NotificationService()
                    # Notify all users who have new matches
                    users_result = await db.execute(select(User).where(User.is_active.is_(True)))
                    users = users_result.scalars().all()

                    match_ids = [m.id for m in new_matches]
                    for user in users:
                        user_match_ids = [
                            m.id for m in new_matches
                            if m.resume and m.resume.user_id == user.id
                        ]
                        if user_match_ids:
                            sent = await notif_svc.send_match_notification(
                                db, user.id, user.email, user_match_ids
                            )
                            logger.info("Notified user {} of {} matches", user.email, sent)

            await db.commit()
            logger.info("Pipeline job completed successfully")

        except Exception:
            await db.rollback()
            logger.exception("Pipeline job failed")


async def process_applications_job() -> None:
    """Process approved matches that don't have applications yet."""
    from app.core.database import async_session_factory
    from app.services.auto_apply import AutoApplyService

    async with async_session_factory() as db:
        try:
            svc = AutoApplyService()
            count = await svc.process_approved_matches(db)
            await db.commit()
            if count:
                logger.info("Processed {} applications", count)
        except Exception:
            await db.rollback()
            logger.exception("Application processing failed")


async def retry_failed_job() -> None:
    """Retry eligible failed applications."""
    from app.core.database import async_session_factory
    from app.services.auto_apply import AutoApplyService

    async with async_session_factory() as db:
        try:
            svc = AutoApplyService()
            retryable = await svc.get_retryable_applications(db)
            for app in retryable:
                await svc.execute_application(db, app)
            await db.commit()
            if retryable:
                logger.info("Retried {} applications", len(retryable))
        except Exception:
            await db.rollback()
            logger.exception("Retry job failed")


def start_scheduler() -> None:
    """Initialize and start the background scheduler."""
    global _scheduler

    settings = get_settings()
    _scheduler = AsyncIOScheduler()

    # Sequential pipeline: scrape → match → notify
    _scheduler.add_job(
        pipeline_job,
        "interval",
        minutes=settings.scrape_interval_minutes,
        id="pipeline",
        name="Scrape→Match→Notify Pipeline",
        max_instances=1,
    )

    # Process approved matches every 5 minutes
    _scheduler.add_job(
        process_applications_job,
        "interval",
        minutes=5,
        id="process_applications",
        name="Process Applications",
        max_instances=1,
    )

    # Retry failed applications every 30 minutes
    _scheduler.add_job(
        retry_failed_job,
        "interval",
        minutes=30,
        id="retry_failed",
        name="Retry Failed Applications",
        max_instances=1,
    )

    _scheduler.start()
    logger.info(
        "Scheduler started — pipeline every {}min, applications every 5min, retries every 30min",
        settings.scrape_interval_minutes,
    )


def stop_scheduler() -> None:
    """Shut down the background scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
    _scheduler = None
