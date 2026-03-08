"""
Abstract base class for scrapers with per-provider rate limiting.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class JobData:
    """Normalized job data returned by all scrapers."""

    title: str = ""
    company: str = ""
    location: str = ""
    description: str = ""
    url: str = ""
    job_type: str = "full_time"
    experience_level: str = "mid"
    remote_status: str = "unknown"
    salary_min: float | None = None
    salary_max: float | None = None


class BaseScraper(ABC):
    """
    Abstract scraper with built-in rate limiting and retry.

    Subclasses set ``rate_limit`` (seconds between requests) and implement ``scrape()``.
    """

    rate_limit: float = 2.0  # seconds between requests
    max_retries: int = 3
    provider_name: str = "base"

    def __init__(self) -> None:
        self._last_request_time: float = 0

    async def _rate_limit_wait(self) -> None:
        """Enforce minimum delay between requests."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    @abstractmethod
    async def scrape(
        self, query: str, location: str, max_pages: int = 5, **kwargs
    ) -> list[dict]:
        """
        Scrape jobs matching the query/location.

        Args:
            query: Search query (e.g. "python developer").
            location: Location filter (e.g. "remote").
            max_pages: Maximum pages to paginate.

        Returns:
            List of job dicts ready for ``ScraperService.store_jobs()``.
        """
        ...
