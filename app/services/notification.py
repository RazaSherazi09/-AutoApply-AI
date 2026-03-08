"""
SMTP notification service with deduplication.

Prevents duplicate notifications via content hash in the ``notifications`` table.
"""

from __future__ import annotations

import hashlib
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.notification import Notification


class NotificationService:
    """Sends SMTP email notifications with dedup tracking."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def _compute_hash(self, user_id: int, notif_type: str, reference_id: str) -> str:
        """Generate dedup hash: sha256(user_id + type + reference_id)."""
        raw = f"{user_id}:{notif_type}:{reference_id}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def _is_duplicate(
        self, db: AsyncSession, content_hash: str
    ) -> bool:
        """Check if a notification with this hash already exists."""
        result = await db.execute(
            select(Notification.id).where(Notification.content_hash == content_hash)
        )
        return result.scalar_one_or_none() is not None

    async def _record_notification(
        self,
        db: AsyncSession,
        user_id: int,
        notif_type: str,
        reference_id: str,
        content_hash: str,
        message: str,
        channel: str = "EMAIL",
    ) -> None:
        """Store notification record for dedup tracking."""
        notif = Notification(
            user_id=user_id,
            type=notif_type,
            reference_id=reference_id,
            content_hash=content_hash,
            message=message,
            channel=channel,
        )
        db.add(notif)
        await db.flush()

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        attachment_path: str | None = None,
    ) -> None:
        """
        Send an email via SMTP (synchronous — called from async context via run_in_executor).

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            html_body: HTML email body.
            attachment_path: Optional file path to attach.
        """
        s = self.settings
        if not s.smtp_user or not s.smtp_password:
            logger.warning("SMTP not configured — skipping email to {}", to_email)
            return

        msg = MIMEMultipart("alternative")
        msg["From"] = s.smtp_from_email or s.smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        # Optional attachment
        if attachment_path:
            path = Path(attachment_path)
            if path.exists():
                part = MIMEBase("application", "octet-stream")
                part.set_payload(path.read_bytes())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={path.name}",
                )
                msg.attach(part)

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(s.smtp_host, s.smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(s.smtp_user, s.smtp_password)
                server.sendmail(s.smtp_user, to_email, msg.as_string())
            logger.info("Email sent to {}: {}", to_email, subject)
        except Exception:
            logger.exception("Failed to send email to {}", to_email)
            raise

    async def send_match_notification(
        self,
        db: AsyncSession,
        user_id: int,
        user_email: str,
        match_ids: list[int],
    ) -> int:
        """
        Notify user about new pending matches (dedup-safe).

        Args:
            db: Database session.
            user_id: User to notify.
            user_email: Email address.
            match_ids: IDs of new matches.

        Returns:
            Number of notifications actually sent (after dedup).
        """
        sent = 0
        for match_id in match_ids:
            content_hash = self._compute_hash(user_id, "NEW_MATCH", str(match_id))
            if await self._is_duplicate(db, content_hash):
                logger.debug("Skipping duplicate notification for match {}", match_id)
                continue

            subject = f"[AutoApply AI] New Job Match #{match_id}"
            body = f"""
            <html><body>
            <h2>🎯 New Job Match Found!</h2>
            <p>Match <strong>#{match_id}</strong> is waiting for your review.</p>
            <p>Open your <strong>AutoApply Dashboard</strong> to approve or reject.</p>
            <hr>
            <p style="color: #888;">— AutoApply AI</p>
            </body></html>
            """

            try:
                self._send_email(user_email, subject, body)
                await self._record_notification(
                    db, user_id, "NEW_MATCH", str(match_id), content_hash,
                    f"Match #{match_id} notification sent",
                )
                sent += 1
            except Exception:
                logger.exception("Failed to notify match {}", match_id)

        return sent

    async def send_application_status(
        self,
        db: AsyncSession,
        user_id: int,
        user_email: str,
        application_id: int,
        status: str,
    ) -> bool:
        """Notify user about application status change (dedup-safe)."""
        ref = f"{application_id}:{status}"
        content_hash = self._compute_hash(user_id, "APPLICATION_STATUS", ref)

        if await self._is_duplicate(db, content_hash):
            return False

        subject = f"[AutoApply AI] Application #{application_id} — {status}"
        body = f"""
        <html><body>
        <h2>📋 Application Status Update</h2>
        <p>Application <strong>#{application_id}</strong> is now: <strong>{status}</strong></p>
        <hr>
        <p style="color: #888;">— AutoApply AI</p>
        </body></html>
        """

        try:
            self._send_email(user_email, subject, body)
            await self._record_notification(
                db, user_id, "APPLICATION_STATUS", ref, content_hash,
                f"Application #{application_id} status: {status}",
            )
            return True
        except Exception:
            logger.exception("Failed to notify application status {}", application_id)
            return False
