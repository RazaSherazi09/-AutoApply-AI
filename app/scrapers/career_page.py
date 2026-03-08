"""
Career page scraper using Playwright + BeautifulSoup.

Scrapes generic company career pages using configurable CSS selectors.
"""

from __future__ import annotations

from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.scrapers.base import BaseScraper


class CareerPageScraper(BaseScraper):
    """
    Browser-based scraper for company career pages.

    Uses Playwright (via browser pool) to render JS-heavy pages,
    then parses with BeautifulSoup.
    """

    rate_limit = 5.0  # Be respectful to company sites
    provider_name = "career_page"

    async def scrape(
        self,
        query: str,
        location: str,
        max_pages: int = 1,
        career_urls: list[dict] | None = None,
        **kwargs,
    ) -> list[dict]:
        """
        Scrape career pages defined in ``career_urls``.

        Args:
            query: Search keyword to filter on page.
            location: Location filter.
            career_urls: List of dicts with keys:
                - url: The career page URL
                - company: Company name
                - job_link_selector: CSS selector for job links (default: 'a')
                - title_selector: CSS selector for job title within link
                - description_selector: CSS selector for job description

        Returns:
            List of job dicts.
        """
        if not career_urls:
            logger.info("No career page URLs configured — skipping")
            return []

        all_jobs: list[dict] = []

        for config in career_urls:
            try:
                await self._rate_limit_wait()
                jobs = await self._scrape_page(config, query)
                all_jobs.extend(jobs)
            except Exception:
                logger.exception("Failed to scrape career page: {}", config.get("url"))

        logger.info("Career page scraper found {} jobs", len(all_jobs))
        return all_jobs

    @retry(wait=wait_exponential(min=2, max=30), stop=stop_after_attempt(3))
    async def _scrape_page(self, config: dict, query: str) -> list[dict]:
        """Scrape a single career page."""
        from app.worker.browser_pool import BrowserPool

        url = config["url"]
        company = config.get("company", "Unknown")
        link_selector = config.get("job_link_selector", "a[href*='job'], a[href*='career'], a[href*='position']")

        pool = BrowserPool.get_instance()
        async with pool.acquire_page() as page:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            content = await page.content()

        soup = BeautifulSoup(content, "html.parser")
        jobs: list[dict] = []

        links = soup.select(link_selector)
        for link in links:
            title = link.get_text(strip=True)
            href = link.get("href", "")

            # Filter by query keyword
            if query.lower() not in title.lower():
                continue

            # Make URL absolute
            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(url, href)

            if not href or not title:
                continue

            jobs.append({
                "title": title,
                "company": company,
                "location": "",  # Often not available on listing pages
                "description": "",  # Would need a detail page scrape
                "url": href,
                "remote_status": "unknown",
            })

        logger.debug("Career page {} yielded {} jobs matching '{}'", url, len(jobs), query)
        return jobs
