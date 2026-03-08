"""
Auto-apply execution service.

Dispatches approved matches to the correct handler (email or web),
enforces daily application cap, and handles retry logic.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.application import Application
from app.models.match import Match


class DailyLimitReached(Exception):
    """Raised when the daily application cap is hit."""
    pass


class AutoApplyService:
    """Coordinates application execution with safety limits."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def _check_daily_limit(self, db: AsyncSession) -> int:
        """
        Check current daily application count.

        Returns:
            Number of applications sent/submitted today.

        Raises:
            DailyLimitReached: If cap is hit.
        """
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        result = await db.execute(
            select(func.count(Application.id)).where(
                Application.applied_at >= today_start,
                Application.status.in_(["SENT", "SUBMITTED"]),
            )
        )
        count = result.scalar() or 0

        if count >= self.settings.max_applications_per_day:
            raise DailyLimitReached(
                f"Daily limit reached: {count}/{self.settings.max_applications_per_day}"
            )
        return count

    def _detect_handler_type(self, url: str) -> str:
        """Detect the appropriate form handler based on the application URL."""
        url_lower = url.lower()
        if "linkedin.com" in url_lower:
            return "LINKEDIN"
        if "greenhouse.io" in url_lower or "boards.greenhouse" in url_lower:
            return "GREENHOUSE"
        if "lever.co" in url_lower or "jobs.lever" in url_lower:
            return "LEVER"
        if "myworkdayjobs.com" in url_lower or "workday" in url_lower:
            return "WORKDAY"
        return "GENERIC"

    async def create_application(
        self,
        db: AsyncSession,
        match: Match,
        method: str = "WEB",
    ) -> Application:
        """
        Create an application record for an approved match.

        Args:
            db: Database session.
            match: The approved match to apply for.
            method: EMAIL or WEB.

        Returns:
            New Application record.

        Raises:
            DailyLimitReached: If daily cap is hit.
        """
        await self._check_daily_limit(db)

        url = match.job.url if match.job else ""
        handler_type = "EMAIL" if method == "EMAIL" else self._detect_handler_type(url)

        application = Application(
            match_id=match.id,
            method=method,
            handler_type=handler_type,
            status="PENDING",
        )
        db.add(application)
        await db.flush()
        logger.info(
            "Created application #{} for match #{} (handler={})",
            application.id, match.id, handler_type,
        )
        return application

    async def execute_application(
        self,
        db: AsyncSession,
        application: Application,
    ) -> None:
        """
        Execute an application (email or web).

        On failure, schedules a retry with exponential backoff.
        """
        try:
            await self._check_daily_limit(db)

            if application.method == "EMAIL":
                await self._apply_via_email(application)
            else:
                await self._apply_via_web(application)

            application.status = "SUBMITTED"
            application.applied_at = datetime.now(timezone.utc)
            logger.info("Application #{} submitted successfully", application.id)

        except DailyLimitReached:
            logger.warning("Daily limit reached — deferring application #{}", application.id)
            application.next_retry_at = datetime.now(timezone.utc) + timedelta(hours=1)

        except Exception as e:
            application.retry_count += 1
            application.error_log = str(e)

            if application.retry_count >= application.max_retries:
                application.status = "FAILED"
                logger.error("Application #{} permanently failed after {} retries: {}",
                             application.id, application.retry_count, e)
            else:
                # Exponential backoff: 1h, 4h, 16h
                delay_hours = 4 ** (application.retry_count - 1)
                application.next_retry_at = datetime.now(timezone.utc) + timedelta(hours=delay_hours)
                logger.warning(
                    "Application #{} failed (attempt {}), retry in {}h: {}",
                    application.id, application.retry_count, delay_hours, e,
                )

        await db.flush()

    async def _apply_via_email(self, application: Application) -> None:
        """Send application via SMTP with resume attachment."""
        from app.services.notification import NotificationService

        notif = NotificationService()
        match = application.match
        job = match.job if match else None
        resume = match.resume if match else None

        if not job or not resume:
            raise ValueError("Match missing job or resume data")

        subject = f"Application for {job.title} — {job.company}"
        body = f"""
        <html><body>
        <p>Dear Hiring Manager,</p>
        <p>I am writing to express my interest in the <strong>{job.title}</strong> position
        at <strong>{job.company}</strong>.</p>
        <p>Please find my resume attached for your review.</p>
        <p>Best regards</p>
        </body></html>
        """

        notif._send_email(
            to_email=job.url,  # For email applications, URL is the email address
            subject=subject,
            html_body=body,
            attachment_path=resume.file_path,
        )
        application.status = "SENT"

    async def _apply_via_web(self, application: Application) -> None:
        """Apply via Playwright browser automation."""
        from app.services.form_filler import FormFillerDispatcher

        match = application.match
        job = match.job if match else None
        resume = match.resume if match else None

        if not job or not resume:
            raise ValueError("Match missing job or resume data")

        dispatcher = FormFillerDispatcher()
        result = await dispatcher.fill_from_url(
            url=job.url,
            resume=resume,
        )

        if result.status == "MANUAL_REVIEW":
            application.status = "MANUAL_REVIEW"
            application.error_log = f"Low confidence ({result.confidence:.2f})"
            logger.warning("Application #{} flagged for manual review", application.id)
        elif result.status == "SUCCESS":
            application.status = "SUBMITTED"
        else:
            raise RuntimeError(f"Form fill failed: {result.error}")

    async def get_retryable_applications(self, db: AsyncSession) -> list[Application]:
        """Get applications eligible for retry (next_retry_at <= now, not yet max retries)."""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(Application).where(
                Application.next_retry_at <= now,
                Application.retry_count < Application.max_retries,
                Application.status != "SUBMITTED",
                Application.status != "FAILED",
                Application.status != "SENT",
            )
        )
        return list(result.scalars().all())

    async def process_approved_matches(self, db: AsyncSession) -> int:
        """Create and execute applications for all newly approved matches."""
        result = await db.execute(
            select(Match)
            .where(Match.status == "APPROVED")
            .outerjoin(Application)
            .where(Application.id.is_(None))
        )
        approved_matches = result.scalars().all()

        count = 0
        for match in approved_matches:
            try:
                app = await self.create_application(db, match)
                await self.execute_application(db, app)
                count += 1
            except DailyLimitReached:
                logger.warning("Daily limit reached — stopping application processing")
                break
            except Exception:
                logger.exception("Error processing match #{}", match.id)

        return count
