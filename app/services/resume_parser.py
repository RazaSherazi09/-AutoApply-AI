"""
Resume parsing service: PDF text extraction + spaCy NER + embedding.

Supports resume versioning — new uploads increment version with parent_id link.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import fitz  # PyMuPDF
from loguru import logger

from app.services.embedding import EmbeddingService


# ── Curated skills (word-boundary matched, not substring) ──
KNOWN_SKILLS: dict[str, str] = {
    # language → canonical form
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "java": "java",
    "c++": "cpp",
    "c#": "csharp",
    "golang": "go",
    "go": "go",
    "rust": "rust",
    "ruby": "ruby",
    "php": "php",
    "swift": "swift",
    "kotlin": "kotlin",
    "scala": "scala",
    "matlab": "matlab",
    "perl": "perl",
    # frontend
    "html": "html",
    "css": "css",
    "react": "react",
    "reactjs": "react",
    "react.js": "react",
    "angular": "angular",
    "vue": "vue",
    "vue.js": "vue",
    "vuejs": "vue",
    "svelte": "svelte",
    "next.js": "nextjs",
    "nextjs": "nextjs",
    "nuxt.js": "nuxtjs",
    "nuxtjs": "nuxtjs",
    # backend
    "node.js": "nodejs",
    "nodejs": "nodejs",
    "express": "express",
    "express.js": "express",
    "fastapi": "fastapi",
    "django": "django",
    "flask": "flask",
    "spring": "spring",
    "spring boot": "spring boot",
    ".net": "dotnet",
    "asp.net": "dotnet",
    # databases
    "sql": "sql",
    "mysql": "mysql",
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "mongodb": "mongodb",
    "redis": "redis",
    "elasticsearch": "elasticsearch",
    "sqlite": "sqlite",
    "oracle": "oracle",
    "dynamodb": "dynamodb",
    # cloud / devops
    "aws": "aws",
    "azure": "azure",
    "gcp": "gcp",
    "google cloud": "gcp",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "terraform": "terraform",
    "ansible": "ansible",
    "jenkins": "jenkins",
    "ci/cd": "ci/cd",
    "github actions": "github actions",
    "gitlab ci": "gitlab ci",
    # data / ML
    "machine learning": "machine learning",
    "deep learning": "deep learning",
    "nlp": "nlp",
    "natural language processing": "nlp",
    "computer vision": "computer vision",
    "tensorflow": "tensorflow",
    "pytorch": "pytorch",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "pandas": "pandas",
    "numpy": "numpy",
    "scipy": "scipy",
    "spark": "spark",
    "hadoop": "hadoop",
    "kafka": "kafka",
    "airflow": "airflow",
    "dbt": "dbt",
    "snowflake": "snowflake",
    "bigquery": "bigquery",
    "redshift": "redshift",
    "databricks": "databricks",
    "tableau": "tableau",
    "power bi": "power bi",
    # protocols / architecture
    "rest": "rest",
    "restful": "rest",
    "graphql": "graphql",
    "grpc": "grpc",
    "microservices": "microservices",
    # tools
    "git": "git",
    "linux": "linux",
    "bash": "bash",
    "powershell": "powershell",
    "agile": "agile",
    "scrum": "scrum",
    "jira": "jira",
    "confluence": "confluence",
    "figma": "figma",
    "selenium": "selenium",
    "playwright": "playwright",
    "cypress": "cypress",
    "pytest": "pytest",
    "junit": "junit",
}

# Skills that need word-boundary matching to avoid false positives
# (e.g. "go" matches "going", "r" matches "experience")
SHORT_SKILLS = {"go", "r", "sql", "git", "vue", "dbt", "aws", "gcp", "css", "nlp", "php"}


class ResumeParser:
    """Extracts structured information from PDF resumes."""

    _instance: ResumeParser | None = None

    def __init__(self) -> None:
        try:
            import spacy
            logger.info("Loading spaCy model: en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        except (ImportError, OSError):
            logger.warning("spaCy not found. Using Mock NLP extraction.")
            self.nlp = None
            
        self.embedding_svc = EmbeddingService.get_instance()

    @classmethod
    def get_instance(cls) -> ResumeParser:
        """Singleton to avoid reloading spaCy + embedding model on every upload."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def extract_text(self, pdf_path: str | Path) -> str:
        """Extract all text from a PDF file using PyMuPDF."""
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")

        text_parts: list[str] = []
        with fitz.open(str(path)) as doc:
            for page in doc:
                text_parts.append(page.get_text())

        full_text = "\n".join(text_parts).strip()
        logger.debug("Extracted {} chars from {}", len(full_text), path.name)
        return full_text

    def extract_entities(self, text: str) -> dict:
        """
        Extract structured entities from resume text using spaCy + regex + keyword matching.

        Returns dict with: name, email, phone, skills, experience_years, education, summary.
        """
        # ── Name extraction ──
        # Strategy: check first 5 lines for a PERSON entity, or use the first
        # non-blank line if no entity found (most resumes start with the name).
        name = ""
        first_lines = text.split("\n")[:10]

        # Try spaCy on just the header
        header_text = "\n".join(first_lines)
        if self.nlp:
            header_doc = self.nlp(header_text)
            for ent in header_doc.ents:
                if ent.label_ == "PERSON":
                    candidate = ent.text.strip()
                    # Validate: likely a name (2-4 words, no digits, not too long)
                    words = candidate.split()
                    if 1 <= len(words) <= 4 and not any(c.isdigit() for c in candidate) and len(candidate) < 60:
                        name = candidate
                        break

        # Fallback: first non-blank, non-email, non-phone line
        if not name:
            for line in first_lines:
                stripped = line.strip()
                if (
                    stripped
                    and not re.search(r"[@.]\w", stripped)  # not email
                    and not re.search(r"\d{3}", stripped)  # not phone-like
                    and len(stripped) < 50
                    and len(stripped.split()) <= 4
                ):
                    name = stripped
                    break

        # ── Email extraction ──
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
        email = email_match.group(0) if email_match else ""

        # ── Phone extraction ──
        phone_match = re.search(
            r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}", text
        )
        phone = phone_match.group(0).strip() if phone_match else ""

        # ── Skill extraction (word-boundary aware) ──
        text_lower = text.lower()
        found_skills: set[str] = set()

        for keyword, canonical in KNOWN_SKILLS.items():
            if keyword in SHORT_SKILLS:
                # Use word boundary matching for short keywords
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills.add(canonical)
            else:
                # Direct substring match is fine for longer keywords
                if keyword in text_lower:
                    found_skills.add(canonical)

        skills = sorted(found_skills)

        # ── Experience years ──
        experience_years = 0.0
        year_patterns = re.findall(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)?", text_lower)
        if year_patterns:
            experience_years = max(float(y) for y in year_patterns)

        # ── Education (simple heuristic) ──
        education: list[str] = []
        edu_patterns = [
            r"(?:bachelor|b\.?s\.?|b\.?a\.?|master|m\.?s\.?|m\.?a\.?|ph\.?d|doctorate|mba)\s*(?:of|in|,)?\s*[\w\s]{0,50}",
        ]
        for pat in edu_patterns:
            for match in re.finditer(pat, text_lower):
                edu_text = match.group(0).strip()
                if edu_text and edu_text not in education:
                    education.append(edu_text.title())

        # ── Summary (first paragraph-like block after name) ──
        summary = ""
        lines = text.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if len(stripped) > 80 and i > 0:  # Likely a summary/objective paragraph
                summary = stripped[:500]
                break

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "skills": skills,
            "experience_years": experience_years,
            "education": education,
            "summary": summary,
        }

    def parse_resume(self, pdf_path: str | Path) -> dict:
        """
        Full resume parsing pipeline: text extraction → NER → embedding.

        Returns dict with: raw_text, structured_data (JSON string), embedding (bytes).
        """
        raw_text = self.extract_text(pdf_path)

        if not raw_text.strip():
            logger.warning("Empty text extracted from {}", pdf_path)
            entities = {
                "name": "", "email": "", "phone": "",
                "skills": [], "experience_years": 0.0,
                "education": [], "summary": "",
            }
            return {
                "raw_text": "",
                "structured_data": json.dumps(entities),
                "embedding": EmbeddingService.to_bytes(
                    self.embedding_svc.encode("empty resume")
                ),
            }

        entities = self.extract_entities(raw_text)

        # Generate embedding from full text
        embedding_vec = self.embedding_svc.encode(raw_text[:8000])  # Limit token input
        embedding_bytes = EmbeddingService.to_bytes(embedding_vec)

        logger.info(
            "Parsed resume: name='{}', email='{}', skills={}, exp={}yr",
            entities.get("name", "?"),
            entities.get("email", "?"),
            len(entities.get("skills", [])),
            entities.get("experience_years", 0),
        )

        return {
            "raw_text": raw_text,
            "structured_data": json.dumps(entities),
            "embedding": embedding_bytes,
        }
