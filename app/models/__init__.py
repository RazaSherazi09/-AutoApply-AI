"""Re-export all models for Alembic auto-detection and convenience imports."""

from app.models.base import Base
from app.models.user import User
from app.models.resume import Resume
from app.models.job import Job
from app.models.match import Match
from app.models.application import Application
from app.models.preference import Preference
from app.models.notification import Notification
from app.models.setting import Setting
from app.models.scraper_run import ScraperRun

__all__ = [
    "Base",
    "User",
    "Resume",
    "Job",
    "Match",
    "Application",
    "Preference",
    "Notification",
    "Setting",
    "ScraperRun",
]
