"""
Workday public job API scraper.

Endpoint pattern: https://{company}.wd5.myworkdayjobs.com/wday/cxs/{company}/{site}/jobs
"""

from __future__ import annotations

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.scrapers.base import BaseScraper


# Default Workday sites to scrape
DEFAULT_SITES: list[dict] = [
    # {"company": "salesforce", "subdomain": "salesforce", "site": "Futures"}
]


class WorkdayAPIScraper(BaseScraper):
    """Scrapes job listings from Workday's public JSON endpoint."""

    rate_limit = 3.0  # Workday can be sensitive to rate
    provider_name = "workday"

    @retry(wait=wait_exponential(min=2, max=60), stop=stop_after_attempt(3))
    async def _fetch_jobs(
        self, subdomain: str, company: str, site: str, offset: int = 0, limit: int = 20
    ) -> dict:
        """Fetch jobs from Workday JSON endpoint."""
        await self._rate_limit_wait()

        url = f"https://{subdomain}.wd5.myworkdayjobs.com/wday/cxs/{company}/{site}/jobs"
        payload = {
            "appliedFacets": {},
            "limit": limit,
            "offset": offset,
            "searchText": "",
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def scrape(
        self,
        query: str,
        location: str,
        max_pages: int = 5,
        sites: list[dict] | None = None,
        **kwargs,
    ) -> list[dict]:
        """
        Scrape Workday sites for matching jobs.

        Args:
            query: Keyword to filter by.
            location: Location filter.
            sites: List of dicts with keys: company, subdomain, site.
        """
        site_list = sites or DEFAULT_SITES
        if not site_list:
            logger.info("No Workday sites configured — skipping")
            return []

        all_jobs: list[dict] = []

        for site_config in site_list:
            company = site_config["company"]
            subdomain = site_config.get("subdomain", company)
            site = site_config["site"]

            try:
                offset = 0
                for page_num in range(max_pages):
                    data = await self._fetch_jobs(subdomain, company, site, offset)
                    postings = data.get("jobPostings", [])

                    if not postings:
                        break

                    for item in postings:
                        title = item.get("title", "")
                        if query.lower() not in title.lower():
                            continue

                        loc = item.get("locationsText", "")
                        posted_on = item.get("postedOn", "")

                        # Build URL
                        external_path = item.get("externalPath", "")
                        job_url = (
                            f"https://{subdomain}.wd5.myworkdayjobs.com/en-US/{site}{external_path}"
                            if external_path else ""
                        )

                        job = {
                            "title": title,
                            "company": company.replace("-", " ").title(),
                            "location": loc,
                            "description": item.get("bulletFields", [""])[0] if item.get("bulletFields") else "",
                            "url": job_url,
                            "remote_status": "remote" if "remote" in loc.lower() else "onsite",
                        }
                        all_jobs.append(job)

                    offset += len(postings)
                    total = data.get("total", 0)
                    if offset >= total:
                        break

                logger.debug("Workday site '{}/{}': scraped", company, site)

            except Exception:
                logger.exception("Workday site '{}/{}' failed", company, site)

        logger.info("Workday scraped {} total jobs", len(all_jobs))
        return all_jobs
