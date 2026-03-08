"""
Greenhouse Boards API scraper (public JSON, no auth needed).

Endpoint: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
"""

from __future__ import annotations

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.scrapers.base import BaseScraper


# Default boards to scrape (users can configure more)
DEFAULT_BOARDS: list[str] = [
    # Add company board tokens here, e.g. "stripe", "figma"
]


class GreenhouseAPIScraper(BaseScraper):
    """Scrapes job listings from Greenhouse public board API."""

    rate_limit = 1.5
    provider_name = "greenhouse"

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    @retry(wait=wait_exponential(min=1, max=30), stop=stop_after_attempt(3))
    async def _fetch_board(self, board_token: str) -> list[dict]:
        """Fetch all jobs from a Greenhouse board."""
        await self._rate_limit_wait()

        url = f"{self.BASE_URL}/{board_token}/jobs"
        params = {"content": "true"}  # Include job description HTML

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        return data.get("jobs", [])

    async def scrape(
        self,
        query: str,
        location: str,
        max_pages: int = 5,
        boards: list[str] | None = None,
        **kwargs,
    ) -> list[dict]:
        """
        Scrape Greenhouse boards for matching jobs.

        Args:
            query: Keyword to filter by.
            location: Location filter.
            boards: List of board tokens to scrape.
        """
        board_list = boards or DEFAULT_BOARDS
        if not board_list:
            logger.info("No Greenhouse boards configured — skipping")
            return []

        all_jobs: list[dict] = []

        for board in board_list:
            try:
                raw_jobs = await self._fetch_board(board)

                for item in raw_jobs:
                    title = item.get("title", "")
                    # Filter by query
                    if query.lower() not in title.lower():
                        continue

                    # Extract location
                    loc = item.get("location", {}).get("name", "")
                    if location.lower() not in loc.lower() and location.lower() != "remote":
                        if "remote" not in loc.lower():
                            continue

                    # Parse description (HTML → text)
                    desc_html = item.get("content", "")
                    from bs4 import BeautifulSoup
                    desc = BeautifulSoup(desc_html, "html.parser").get_text(separator=" ", strip=True)

                    job = {
                        "title": title,
                        "company": board.replace("-", " ").title(),
                        "location": loc,
                        "description": desc,
                        "url": item.get("absolute_url", ""),
                        "remote_status": "remote" if "remote" in loc.lower() else "onsite",
                    }
                    all_jobs.append(job)

                logger.debug("Greenhouse board '{}': {} matching jobs", board, len(raw_jobs))

            except Exception:
                logger.exception("Greenhouse board '{}' failed", board)

        logger.info("Greenhouse scraped {} total jobs", len(all_jobs))
        return all_jobs
