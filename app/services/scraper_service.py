"""
Scraper orchestration service.

Coordinates all scraper providers, handles deduplication via composite hash,
extracts skills from new jobs, generates embeddings, and logs scraper runs.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.scraper_run import ScraperRun
from app.services.embedding import EmbeddingService
from app.services.job_skill_extractor import JobSkillExtractor


class ScraperService:
    """
    Orchestrates scrapers, deduplicates results, enriches with embeddings
    and extracted skills, and records execution metrics.
    """

    def __init__(self) -> None:
        self.embedding_svc = EmbeddingService.get_instance()
        self.skill_extractor = JobSkillExtractor()

    @staticmethod
    def compute_content_hash(title: str, company: str, location: str) -> str:
        """Composite dedup hash: sha256(title + company + location)."""
        raw = f"{title.lower().strip()}|{company.lower().strip()}|{location.lower().strip()}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def store_jobs(
        self,
        db: AsyncSession,
        user_id: int,
        jobs_data: list[dict],
        provider: str,
    ) -> tuple[int, int]:
        """
        Store scraped jobs, skipping duplicates.

        For each new job:
        1. Compute content_hash for dedup
        2. Extract skills via JobSkillExtractor
        3. Generate embedding via EmbeddingService

        Args:
            db: Database session.
            jobs_data: List of job dicts with title, company, location, etc.
            provider: Source provider name.

        Returns:
            Tuple of (total_found, new_stored).
        """
        # Load existing hashes for fast dedup, scoped by user
        result = await db.execute(select(Job.content_hash).where(Job.user_id == user_id))
        existing_hashes: set[str] = {row[0] for row in result.all()}

        new_count = 0
        for data in jobs_data:
            content_hash = self.compute_content_hash(
                data.get("title", ""),
                data.get("company", ""),
                data.get("location", ""),
            )

            if content_hash in existing_hashes:
                continue

            # Extract skills
            description = data.get("description", "")
            extracted_skills = self.skill_extractor.extract(description)

            # Generate embedding
            embed_text = f"{data.get('title', '')} {data.get('company', '')} {description}"
            embedding_vec = self.embedding_svc.encode(embed_text)
            embedding_bytes = EmbeddingService.to_bytes(embedding_vec)

            job = Job(
                user_id=user_id,
                title=data.get("title", ""),
                company=data.get("company", ""),
                location=data.get("location", ""),
                description=description,
                url=data.get("url", ""),
                content_hash=content_hash,
                source=provider,
                job_type=data.get("job_type", "full_time"),
                experience_level=data.get("experience_level", "mid"),
                remote_status=data.get("remote_status", "unknown"),
                salary_min=data.get("salary_min"),
                salary_max=data.get("salary_max"),
                extracted_skills=json.dumps(extracted_skills),
                embedding=embedding_bytes,
            )
            db.add(job)
            existing_hashes.add(content_hash)
            new_count += 1

        if new_count:
            await db.flush()

        logger.info(
            "Provider {}: found={}, new={}",
            provider, len(jobs_data), new_count,
        )
        return len(jobs_data), new_count

    async def scrape_all(
        self,
        db: AsyncSession,
        user_id: int,
        query: str = "software engineer",
        location: str = "remote",
    ) -> list[ScraperRun]:
        """
        Run all configured scrapers and record execution metrics.

        Returns:
            List of ScraperRun records for monitoring.
        """
        from app.scrapers.adzuna import AdzunaScraper
        from app.scrapers.greenhouse_api import GreenhouseAPIScraper
        from app.scrapers.lever_api import LeverAPIScraper
        from app.scrapers.linkedin import LinkedInScraper
        from app.scrapers.workday_api import WorkdayAPIScraper

        scrapers = [
            ("linkedin", LinkedInScraper()),
            ("adzuna", AdzunaScraper()),
            ("greenhouse", GreenhouseAPIScraper()),
            ("lever", LeverAPIScraper()),
            ("workday", WorkdayAPIScraper()),
        ]

        runs: list[ScraperRun] = []

        for provider_name, scraper in scrapers:
            started_at = datetime.now(timezone.utc)
            run = ScraperRun(
                provider=provider_name,
                status="SUCCESS",
                started_at=started_at,
            )

            try:
                jobs_data = await scraper.scrape(query=query, location=location)
                total, new = await self.store_jobs(db, user_id, jobs_data, provider_name)

                run.jobs_found = total
                run.jobs_new = new
                run.status = "SUCCESS"

            except Exception as e:
                run.status = "FAILED"
                run.error_log = str(e)
                run.jobs_found = 0
                run.jobs_new = 0
                logger.exception("Scraper {} failed", provider_name)

            finally:
                run.finished_at = datetime.now(timezone.utc)
                run.duration_seconds = (
                    run.finished_at - started_at
                ).total_seconds()
                db.add(run)
                runs.append(run)

        await db.flush()
        return runs
