"""
Hybrid matching engine.

Score = 0.6·semantic + 0.2·skill_overlap + 0.1·title_match + 0.1·location_match
All components normalized to [0, 1] before weighting.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from difflib import SequenceMatcher

import numpy as np
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.job import Job
from app.models.match import Match
from app.models.preference import Preference
from app.models.resume import Resume
from app.services.embedding import EmbeddingService


@dataclass
class MatchScores:
    """Breakdown of the hybrid match score."""

    semantic: float
    skill: float
    title: float
    location: float
    final: float


class MatcherService:
    """Computes hybrid match scores between resumes and jobs."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.embedding_svc = EmbeddingService.get_instance()

    def _compute_semantic_score(
        self, resume_emb: np.ndarray, job_emb: np.ndarray
    ) -> float:
        """Cosine similarity clamped to [0, 1]."""
        raw = EmbeddingService.cosine_similarity(resume_emb, job_emb)
        return max(0.0, min(1.0, raw))

    def _compute_skill_score(
        self, resume_skills: set[str], job_skills: set[str]
    ) -> float:
        """Jaccard similarity: |intersection| / |union|, naturally [0, 1]."""
        if not resume_skills and not job_skills:
            return 0.0
        union = resume_skills | job_skills
        if not union:
            return 0.0
        return len(resume_skills & job_skills) / len(union)

    def _compute_title_score(
        self, desired_titles: list[str], job_title: str
    ) -> float:
        """Best SequenceMatcher ratio across desired titles, [0, 1]."""
        if not desired_titles:
            return 0.5  # neutral if no preference set
        job_lower = job_title.lower()
        scores = [
            SequenceMatcher(None, dt.lower(), job_lower).ratio()
            for dt in desired_titles
        ]
        return max(scores) if scores else 0.0

    def _compute_location_score(
        self, desired_locations: list[str], job_location: str, remote_only: bool
    ) -> float:
        """
        Location matching with remote bonus.

        Returns:
            1.0 — exact match or remote when remote_only
            0.7 — job is remote (but user didn't set remote_only)
            0.5 — partial match (city or state overlap)
            0.0 — no match
        """
        job_loc_lower = job_location.lower()
        is_remote = any(
            kw in job_loc_lower for kw in ("remote", "anywhere", "distributed")
        )

        if remote_only:
            return 1.0 if is_remote else 0.0

        if is_remote:
            return 0.7

        if not desired_locations:
            return 0.5  # neutral

        for loc in desired_locations:
            loc_lower = loc.lower()
            if loc_lower in job_loc_lower or job_loc_lower in loc_lower:
                return 1.0
            # Partial match: check city/state overlap
            loc_parts = set(loc_lower.split())
            job_parts = set(job_loc_lower.split())
            if loc_parts & job_parts:
                return 0.5

        return 0.0

    def compute_hybrid_score(
        self,
        resume: Resume,
        job: Job,
        preferences: Preference | None,
    ) -> MatchScores:
        """
        Compute the full hybrid match score.

        All 4 sub-scores are normalized to [0, 1] before weighting.
        """
        # Decode embeddings
        resume_emb = EmbeddingService.from_bytes(resume.embedding) if resume.embedding else np.zeros(384)
        job_emb = EmbeddingService.from_bytes(job.embedding) if job.embedding else np.zeros(384)

        # Parse skills
        resume_data = json.loads(resume.structured_data) if resume.structured_data else {}
        resume_skills = set(s.lower() for s in resume_data.get("skills", []))
        job_skills_raw = json.loads(job.extracted_skills) if job.extracted_skills else []
        job_skills = set(s.lower() for s in job_skills_raw)

        # Parse preferences
        desired_titles: list[str] = []
        desired_locations: list[str] = []
        remote_only = False
        if preferences:
            desired_titles = json.loads(preferences.desired_titles) if preferences.desired_titles else []
            desired_locations = json.loads(preferences.desired_locations) if preferences.desired_locations else []
            remote_only = preferences.remote_only

        # Compute sub-scores
        semantic = self._compute_semantic_score(resume_emb, job_emb)
        skill = self._compute_skill_score(resume_skills, job_skills)
        title = self._compute_title_score(desired_titles, job.title)
        location = self._compute_location_score(desired_locations, job.location, remote_only)

        # Weighted final score
        s = self.settings
        final = (
            s.match_weight_semantic * semantic
            + s.match_weight_skill * skill
            + s.match_weight_title * title
            + s.match_weight_location * location
        )

        return MatchScores(
            semantic=round(semantic, 4),
            skill=round(skill, 4),
            title=round(title, 4),
            location=round(location, 4),
            final=round(final, 4),
        )

    async def match_all_pending(self, db: AsyncSession) -> list[Match]:
        """
        Match all unmatched jobs against all active resumes.

        Only creates matches above the configured threshold. Checks for
        required keywords in the job description.

        Returns:
            List of newly created Match records.
        """
        settings = self.settings

        # Get latest resume per user (highest version)
        resumes_result = await db.execute(select(Resume))
        all_resumes = resumes_result.scalars().all()

        # Get jobs that don't yet have matches for these resumes
        jobs_result = await db.execute(select(Job))
        all_jobs = jobs_result.scalars().all()

        # Existing match pairs
        existing_result = await db.execute(select(Match.job_id, Match.resume_id))
        existing_pairs = {(r.job_id, r.resume_id) for r in existing_result.all()}

        new_matches: list[Match] = []
        required_kws = settings.required_keywords_list

        for resume in all_resumes:
            # Load user preferences
            pref_result = await db.execute(
                select(Preference).where(Preference.user_id == resume.user_id)
            )
            preferences = pref_result.scalar_one_or_none()

            for job in all_jobs:
                if (job.id, resume.id) in existing_pairs:
                    continue

                # Required keyword check
                if required_kws:
                    desc_lower = job.description.lower()
                    if not all(kw in desc_lower for kw in required_kws):
                        continue

                scores = self.compute_hybrid_score(resume, job, preferences)

                if scores.final >= settings.match_threshold:
                    match = Match(
                        job_id=job.id,
                        resume_id=resume.id,
                        semantic_score=scores.semantic,
                        skill_score=scores.skill,
                        title_score=scores.title,
                        location_score=scores.location,
                        final_score=scores.final,
                        status="PENDING_APPROVAL",
                    )
                    db.add(match)
                    new_matches.append(match)

        if new_matches:
            await db.flush()
            logger.info("Created {} new matches above threshold {}", len(new_matches), settings.match_threshold)

        return new_matches
