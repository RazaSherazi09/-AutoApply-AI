"""
Lever public API scraper.

Endpoint: https://api.lever.co/v0/postings/{company}?mode=json
"""

from __future__ import annotations

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.scrapers.base import BaseScraper

# Default companies to scrape (add Lever company slugs)
DEFAULT_COMPANIES: list[str] = [
    # e.g. "netflix", "twitch"
]


class LeverAPIScraper(BaseScraper):
    """Scrapes job listings from Lever's public postings API."""

    rate_limit = 1.5
    provider_name = "lever"

    BASE_URL = "https://api.lever.co/v0/postings"

    @retry(wait=wait_exponential(min=1, max=30), stop=stop_after_attempt(3))
    async def _fetch_company(self, company: str) -> list[dict]:
        """Fetch all postings for a Lever company."""
        await self._rate_limit_wait()

        url = f"{self.BASE_URL}/{company}"
        params = {"mode": "json"}

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    async def scrape(
        self,
        query: str,
        location: str,
        max_pages: int = 5,
        companies: list[str] | None = None,
        **kwargs,
    ) -> list[dict]:
        """
        Scrape Lever companies for matching jobs.

        Args:
            query: Keyword to filter by.
            location: Location filter.
            companies: List of Lever company slugs.
        """
        company_list = companies or DEFAULT_COMPANIES
        if not company_list:
            logger.info("No Lever companies configured — skipping")
            return []

        all_jobs: list[dict] = []

        for company in company_list:
            try:
                raw_postings = await self._fetch_company(company)

                for item in raw_postings:
                    title = item.get("text", "")
                    if query.lower() not in title.lower():
                        continue

                    # Location
                    loc = item.get("categories", {}).get("location", "")
                    if isinstance(loc, list):
                        loc = ", ".join(loc)

                    # Description
                    desc = item.get("descriptionPlain", "") or ""
                    additional = item.get("additionalPlain", "") or ""
                    full_desc = f"{desc}\n{additional}".strip()

                    job = {
                        "title": title,
                        "company": company.replace("-", " ").title(),
                        "location": loc,
                        "description": full_desc,
                        "url": item.get("hostedUrl", "") or item.get("applyUrl", ""),
                        "remote_status": "remote" if "remote" in loc.lower() else "onsite",
                    }
                    all_jobs.append(job)

                logger.debug("Lever company '{}': {} matching postings", company, len(raw_postings))

            except Exception:
                logger.exception("Lever company '{}' failed", company)

        logger.info("Lever scraped {} total jobs", len(all_jobs))
        return all_jobs
