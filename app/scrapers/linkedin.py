"""
LinkedIn public job board scraper (No Auth required).

Scrapes jobs from the public LinkedIn search portal:
https://www.linkedin.com/jobs/search
"""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.scrapers.base import BaseScraper


class LinkedInScraper(BaseScraper):
    """Scrapes job listings from public LinkedIn job search."""

    rate_limit = 2.0  # LinkedIn aggressively blocks, so be gentle
    provider_name = "linkedin"

    BASE_URL = "https://www.linkedin.com/jobs/search"

    @retry(wait=wait_exponential(min=2, max=60), stop=stop_after_attempt(3))
    async def _fetch_page(self, query: str, location: str, start: int) -> str | None:
        """Fetch a single page of job results via HTML."""
        await self._rate_limit_wait()

        # LinkedIn uses 'keywords', 'location', and 'start' for pagination (25 per page)
        params = {
            "keywords": query,
            "location": location,
            "start": start,
            "f_TPR": "r604800", # Past week to get fresh jobs and avoid stale scraped content
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(self.BASE_URL, params=params, headers=headers)
            if resp.status_code == 429:
                logger.warning("LinkedIn rate limited (429) at start={}", start)
                raise Exception("Rate limited")
            resp.raise_for_status()
            return resp.text

    async def scrape(
        self, query: str, location: str, max_pages: int = 2, **kwargs
    ) -> list[dict]:
        """
        Scrape LinkedIn public jobs.
        max_pages is kept low (2) by default since LinkedIn blocks aggressively.
        """
        all_jobs: list[dict] = []
        
        for page_num in range(max_pages):
            start = page_num * 25 # LinkedIn page size is typically 25
            try:
                html = await self._fetch_page(query, location, start)
                if not html:
                    break
                    
                soup = BeautifulSoup(html, "html.parser")
                
                # The public search page uses <ul> with <li> containing job cards
                job_cards = soup.find_all("div", class_="base-card")
                if not job_cards:
                    # Alternative selector depending on A/B testing or layout shifts
                    job_cards = soup.find_all("li", class_="result-card")
                     
                if not job_cards:
                    job_cards = soup.find_all("div", class_="job-search-card")

                if not job_cards:
                    logger.debug("LinkedIn page {} returned no recognizable job cards.", page_num + 1)
                    break

                for card in job_cards:
                    title_elem = card.find("h3", class_="base-search-card__title")
                    company_elem = card.find("h4", class_="base-search-card__subtitle")
                    location_elem = card.find("span", class_="job-search-card__location")
                    url_elem = card.find("a", class_="base-card__full-link")
                    
                    if not title_elem or not url_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    url = url_elem.get("href", "").split("?")[0] # clean URL tracking
                    
                    # Company name is sometimes an anchor tag
                    company = ""
                    if company_elem:
                        company_meta = company_elem.find("a")
                        company = company_meta.get_text(strip=True) if company_meta else company_elem.get_text(strip=True)
                        
                    loc = location_elem.get_text(strip=True) if location_elem else ""

                    # We don't get the full description on the search page, so we use title/company context
                    desc = f"{title} at {company} located in {loc}"
                    
                    remote_status = "unknown"
                    if "remote" in loc.lower() or "remote" in title.lower():
                        remote_status = "remote"
                    elif "hybrid" in loc.lower() or "hybrid" in title.lower():
                        remote_status = "hybrid"

                    job = {
                        "title": title,
                        "company": company,
                        "location": loc,
                        "description": desc,
                        "url": url,
                        "remote_status": remote_status,
                        "salary_min": None,
                        "salary_max": None,
                        "job_type": self._detect_job_type(title),
                        "experience_level": self._detect_experience_level(title),
                    }
                    all_jobs.append(job)

                logger.debug("LinkedIn page {}: {} results", page_num + 1, len(job_cards))
                
                # If we received less than a full page, we've hit the end
                if len(job_cards) < 10: 
                    break

            except Exception as e:
                logger.exception("LinkedIn page {} failed: {}", page_num + 1, e)
                break

        logger.info("LinkedIn scraped {} total jobs", len(all_jobs))
        return all_jobs

    @staticmethod
    def _detect_job_type(title: str) -> str:
        title_lower = title.lower()
        if "part-time" in title_lower or "part time" in title_lower:
            return "part_time"
        if "contract" in title_lower or "freelance" in title_lower:
            return "contract"
        if "intern" in title_lower:
            return "internship"
        return "full_time"

    @staticmethod
    def _detect_experience_level(title: str) -> str:
        title_lower = title.lower()
        if "senior" in title_lower or "sr." in title_lower or "lead" in title_lower:
            return "senior"
        if "junior" in title_lower or "jr." in title_lower or "entry" in title_lower:
            return "entry"
        if "principal" in title_lower or "staff" in title_lower or "architect" in title_lower:
            return "lead"
        if "director" in title_lower or "vp" in title_lower or "executive" in title_lower:
            return "executive"
        return "mid"
