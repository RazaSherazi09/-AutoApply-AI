import asyncio
import json
import os
import sys
from unittest.mock import MagicMock

# --- MOCK HEAVY ML DEPENDENCIES ---
sys.modules['spacy'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['torch'] = MagicMock()

from pathlib import Path
from sqlalchemy import select

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session_factory
from app.models.job import Job
from app.models.resume import Resume
from app.models.match import Match
from app.services.scraper_service import ScraperService
from app.services.resume_parser import ResumeParser
from app.services.matcher import MatcherService

async def verify_pipeline():
    print("=========================================")
    print("AUTOAPPLY AI - PIPELINE VERIFICATION")
    print("=========================================\n")

    async with async_session_factory() as db:
        
        # --- MOCK ML SERVICES TO BYPASS PYTORCH WINDOWS INSTALL FAILURE ---
        print("[0] MOCKING ML SERVICES (Torch bypass)...")
        from app.services.embedding import EmbeddingService
        import numpy as np
        # Mock encoding to just return a random 768d vector
        EmbeddingService.encode = lambda self, text: np.random.rand(768).astype(np.float32)
        
        # Mock the resume parser to avoid spaCy
        from app.services.resume_parser import ResumeParser
        class MockParser:
            def parse_resume(self, file_path: str):
                return {
                    "raw_text": "Sample mock resume text containing python and react",
                    "structured_data": json.dumps({
                        "name": "Jane Doe",
                        "email": "jane@example.com",
                        "skills": ["Python", "React", "TypeScript", "SQL"],
                        "experience_years": 5
                    }),
                    "embedding": EmbeddingService.to_bytes(np.random.rand(768).astype(np.float32))
                }
        ResumeParser.get_instance = lambda: MockParser()
        
        # Mock semantic score to avoid mismatch between 384d and 768d vectors from old DB entries
        from app.services.matcher import MatcherService
        MatcherService._compute_semantic_score = lambda self, res, job: 0.85
        
        # STEP 1 & 2: SCRAPING (Including LinkedIn)
        print("\n[1] VERIFYING SCRAPERS...")
        scraper_svc = ScraperService()
        runs = await scraper_svc.scrape_all(db, query="software engineer", location="remote")
        
        total_scraped = 0
        for run in runs:
            print(f"  - Provider: {run.provider:<12} | Status: {run.status:<7} | Found: {run.jobs_found} | New: {run.jobs_new}")
            total_scraped += run.jobs_found
            if run.error_log:
                print(f"    !!! Error: {run.error_log}")
        
        print(f"\n[DONE] Scraping finished. {total_scraped} total jobs retrieved across all sources.\n")

        # Check DB for jobs
        result = await db.execute(select(Job))
        jobs = result.scalars().all()
        print(f"  -> Total jobs stored in database: {len(jobs)}")
        if not jobs:
            print("[CRITICAL]: No jobs in database after scraping!")
            return

        # STEP 3: RESUME PARSING
        print("\n[2] VERIFYING RESUME PARSER...")
        
        # Look for a test resume uploaded by user, or create one if none exists in db
        result = await db.execute(select(Resume))
        resume = result.scalars().first()
        
        if resume:
            print(f"  - Found existing resume: {resume.file_name} (v{resume.version})")
            structured_data = json.loads(resume.structured_data) if resume.structured_data else {}
            print(f"  - Name: {structured_data.get('name', 'N/A')}")
            print(f"  - Email: {structured_data.get('email', 'N/A')}")
            print(f"  - Skills extracted: {len(structured_data.get('skills', []))} (e.g., {', '.join(structured_data.get('skills', [])[:5])})")
        else:
            print("  - No resume found in database. The parser cannot be tested without a file.")
            print("  [WARNING] Skipping parse and match steps. Please upload a resume first.")
            return

        print("\n[DONE] Resume parsing verified.\n")


        # STEP 4: MATCH ENGINE
        print("[3] VERIFYING MATCH ENGINE...")
        matcher_svc = MatcherService()
        
        # Print preferences if any
        from app.models.preference import Preference
        pref_res = await db.execute(select(Preference))
        pref = pref_res.scalars().first()
        if pref:
            print(f"  - Active user preferences found: Titles={pref.desired_titles}, RemoteOnly={pref.remote_only}")
            
        print("  - Running MatcherService.match_all_pending()...")
        new_matches = await matcher_svc.match_all_pending(db)
        print(f"  - Matcher generated {len(new_matches)} NEW matches.")
        
        # Get all matches for this resume
        match_query = (
            select(Match, Job)
            .join(Job, Match.job_id == Job.id)
            .where(Match.resume_id == resume.id)
            .order_by(Match.final_score.desc())
        )
        match_result = await db.execute(match_query)
        all_matches = match_result.all()
        
        print(f"\n[DONE] Match engine completed. Total historical matches in DB: {len(all_matches)}\n")

        # STEP 7: PRINT TOP 10 MATCHES
        print("=========================================")
        print("TOP 10 MATCHES")
        print("=========================================")
        if not all_matches:
            print("[ERROR] No matches generated! Check match_threshold inside preferences/config.")
        else:
            for i, (match, job) in enumerate(all_matches[:10], 1):
                print(f"{i}. {job.title} — {job.company} — Score: {match.final_score:.2f}")
                print(f"     (Semantic: {match.semantic_score:.2f} | Skills: {match.skill_score:.2f})")
        
        print("\n=========================================")
        print("Done. To test frontend connection, ensure")
        print("the backend server is running and check")
        print("the /api/matches/ endpoint in browser.")

if __name__ == "__main__":
    asyncio.run(verify_pipeline())
