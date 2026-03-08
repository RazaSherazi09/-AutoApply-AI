"""
Adzuna API scraper (free tier).

Docs: https://developer.adzuna.com/docs/search
"""

from __future__ import annotations

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.scrapers.base import BaseScraper, JobData


class AdzunaScraper(BaseScraper):
    """Scrapes job listings from the Adzuna free API."""

    rate_limit = 1.0  # Adzuna is fairly permissive
    provider_name = "adzuna"

    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(self) -> None:
        super().__init__()
        self.settings = get_settings()

    @retry(wait=wait_exponential(min=1, max=60), stop=stop_after_attempt(3))
    async def _fetch_page(
        self, query: str, location: str, page: int
    ) -> dict:
        """Fetch a single page from Adzuna API."""
        await self._rate_limit_wait()

        url = f"{self.BASE_URL}/{self.settings.adzuna_country}/search/{page}"
        params = {
            "app_id": self.settings.adzuna_app_id,
            "app_key": self.settings.adzuna_app_key,
            "what": query,
            "where": location,
            "results_per_page": 50,
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    async def scrape(
        self, query: str, location: str, max_pages: int = 5, **kwargs
    ) -> list[dict]:
        """
        Scrape Adzuna for jobs matching the query.

        Returns list of job dicts.
        """
        if not self.settings.adzuna_app_id or not self.settings.adzuna_app_key:
            logger.warning("Adzuna API credentials not configured — skipping")
            return []

        all_jobs: list[dict] = []

        for page_num in range(1, max_pages + 1):
            try:
                data = await self._fetch_page(query, location, page_num)
                results = data.get("results", [])

                if not results:
                    break

                for item in results:
                    # Detect remote status
                    loc = item.get("location", {})
                    display_name = ", ".join(loc.get("area", [])) if loc.get("area") else ""
                    title = item.get("title", "")
                    desc = item.get("description", "")

                    remote_status = "unknown"
                    combined_text = f"{title} {desc} {display_name}".lower()
                    if "remote" in combined_text:
                        remote_status = "remote"
                    elif "hybrid" in combined_text:
                        remote_status = "hybrid"

                    job = {
                        "title": title,
                        "company": item.get("company", {}).get("display_name", "Unknown"),
                        "location": display_name,
                        "description": desc,
                        "url": item.get("redirect_url", ""),
                        "salary_min": item.get("salary_min"),
                        "salary_max": item.get("salary_max"),
                        "remote_status": remote_status,
                        "job_type": self._detect_job_type(title, desc),
                        "experience_level": self._detect_experience_level(title, desc),
                    }
                    all_jobs.append(job)

                logger.debug("Adzuna page {}: {} results", page_num, len(results))

                # Stop if fewer results than requested (last page)
                if len(results) < 50:
                    break

            except Exception:
                logger.exception("Adzuna page {} failed", page_num)
                break

        logger.info("Adzuna scraped {} total jobs", len(all_jobs))
        return all_jobs

    @staticmethod
    def _detect_job_type(title: str, desc: str) -> str:
        """Heuristic job type detection from title/description."""
        combined = f"{title} {desc}".lower()
        if "part-time" in combined or "part time" in combined:
            return "part_time"
        if "contract" in combined or "freelance" in combined:
            return "contract"
        if "intern" in combined:
            return "internship"
        return "full_time"

    @staticmethod
    def _detect_experience_level(title: str, desc: str) -> str:
        """Heuristic experience level detection."""
        combined = f"{title} {desc}".lower()
        if "senior" in combined or "sr." in combined or "lead" in combined:
            return "senior"
        if "junior" in combined or "jr." in combined or "entry" in combined:
            return "entry"
        if "principal" in combined or "staff" in combined or "architect" in combined:
            return "lead"
        if "director" in combined or "vp" in combined or "executive" in combined:
            return "executive"
        return "mid"
