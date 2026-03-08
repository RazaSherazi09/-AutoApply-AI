"""
Application settings loaded from environment variables via pydantic-settings.
All secrets live in .env — never exposed through the frontend.
"""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration — reads from .env file and environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Project paths ──
    project_root: Path = Path(__file__).resolve().parent.parent.parent
    upload_dir: Path = Path("uploads")
    log_dir: Path = Path("logs")

    # ── Database ──
    database_url: str = "sqlite+aiosqlite:///./autoapply.db"

    # ── JWT Auth ──
    jwt_secret_key: str = "CHANGE_ME_TO_A_RANDOM_SECRET"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 1440  # 24 hours

    # ── SMTP ──
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    # ── Adzuna API ──
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    adzuna_country: str = "us"

    # ── Scraping ──
    scrape_interval_minutes: int = 60

    # ── Matching ──
    match_threshold: float = 0.25
    match_weight_semantic: float = 0.6
    match_weight_skill: float = 0.2
    match_weight_title: float = 0.1
    match_weight_location: float = 0.1
    required_keywords: str = ""  # comma-separated

    # ── Safety ──
    max_applications_per_day: int = 25
    browser_pool_size: int = 3

    # ── Logging ──
    log_level: str = "INFO"
    log_file: str = "logs/autoapply.log"

    # ── Derived helpers ──
    @property
    def required_keywords_list(self) -> list[str]:
        """Parse comma-separated keywords into a list."""
        if not self.required_keywords:
            return []
        return [kw.strip().lower() for kw in self.required_keywords.split(",") if kw.strip()]


def get_settings() -> Settings:
    """Singleton-like settings accessor (cached by pydantic internally)."""
    return Settings()
