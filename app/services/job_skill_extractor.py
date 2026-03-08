"""
Job skill extractor using spaCy noun chunks + keyword filtering.

Extracts technical skills from job descriptions for the skill overlap
component of the hybrid matching algorithm.
"""

from __future__ import annotations

import re
import spacy
from loguru import logger

# ── Normalization map: raw text → canonical skill name ──
NORMALIZE_MAP: dict[str, str] = {
    "c++": "cpp",
    "c#": "csharp",
    "c sharp": "csharp",
    "node.js": "nodejs",
    "node js": "nodejs",
    "react.js": "react",
    "react js": "react",
    "vue.js": "vue",
    "vue js": "vue",
    "next.js": "nextjs",
    "next js": "nextjs",
    "nuxt.js": "nuxtjs",
    "express.js": "express",
    "angular.js": "angular",
    "asp.net": "dotnet",
    ".net": "dotnet",
    "golang": "go",
    "k8s": "kubernetes",
    "postgres": "postgresql",
    "sklearn": "scikit-learn",
    "pyspark": "spark",
    "react native": "react native",
    "spring boot": "spring boot",
    "google cloud": "gcp",
    "machine learning": "machine learning",
    "deep learning": "deep learning",
    "natural language processing": "nlp",
    "artificial intelligence": "ai",
    "computer vision": "computer vision",
    "data science": "data science",
    "data engineering": "data engineering",
    "github actions": "github actions",
    "gitlab ci": "gitlab ci",
    "power bi": "power bi",
    "unit testing": "unit testing",
    "integration testing": "integration testing",
    "mobile development": "mobile development",
    "ux design": "ux design",
    "ui design": "ui design",
}

# ── Curated single-word/simple skills ──
TECH_SKILLS: set[str] = {
    # Languages
    "python", "javascript", "typescript", "java", "rust", "ruby", "php",
    "swift", "kotlin", "scala", "matlab", "perl", "haskell", "lua",
    "dart", "elixir", "clojure", "r",
    # Frontend
    "html", "css", "sass", "less", "react", "angular", "vue", "svelte",
    "nextjs", "nuxtjs", "gatsby", "tailwind", "bootstrap", "webpack", "vite",
    # Backend
    "nodejs", "express", "fastapi", "django", "flask", "spring",
    "rails", "laravel", "gin", "fiber",
    # Databases
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "sqlite", "mariadb", "neo4j", "firestore",
    "supabase",
    # Cloud & DevOps
    "aws", "azure", "gcp", "heroku", "vercel", "docker", "kubernetes",
    "terraform", "ansible", "puppet", "jenkins", "circleci",
    "devops", "sre", "nginx", "apache",
    # Normalized
    "cpp", "csharp", "dotnet", "go",
    # Data & ML
    "tensorflow", "pytorch", "keras", "scikit-learn",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn",
    "spark", "hadoop", "hive", "kafka", "airflow",
    "dbt", "snowflake", "bigquery", "redshift", "databricks",
    "tableau", "looker", "metabase",
    "nlp", "ai",
    # Testing
    "selenium", "playwright", "cypress", "puppeteer",
    "pytest", "jest", "mocha", "junit", "rspec",
    # Tools
    "git", "github", "gitlab", "bitbucket",
    "jira", "confluence", "trello", "agile", "scrum", "kanban",
    "rest", "graphql", "grpc", "websocket", "microservices", "serverless",
    "oauth", "jwt",
    # OS
    "linux", "ubuntu", "bash", "powershell",
    # Mobile
    "flutter", "ionic", "android", "ios",
    # Design
    "figma", "sketch", "photoshop", "illustrator",
    # CI/CD (special chars)
    "ci/cd",
}

# Short skills that need word-boundary matching
SHORT_SKILLS = {"r", "go", "ai", "c", "git", "dbt", "sql", "css", "nlp", "vue", "php", "aws", "gcp", "ios", "jwt", "sre"}


class JobSkillExtractor:
    """
    Extracts technical skills from job description text.

    Uses three strategies:
    1. Pre-processing normalization (c++ → cpp, node.js → nodejs)
    2. spaCy noun chunk + token matching against curated vocabulary
    3. Multi-word skill substring matching
    """

    _instance: JobSkillExtractor | None = None

    def __init__(self) -> None:
        self.nlp = spacy.load("en_core_web_sm")
        logger.info("JobSkillExtractor initialized with {} skills + {} normalizations",
                     len(TECH_SKILLS), len(NORMALIZE_MAP))

    @classmethod
    def get_instance(cls) -> JobSkillExtractor:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def extract(self, text: str) -> list[str]:
        """
        Extract technical skills from job description text.

        Returns:
            Sorted, deduplicated list of canonical skill names.
        """
        if not text or not text.strip():
            return []

        text_lower = text.lower()
        skills: set[str] = set()

        # Strategy 1: Direct normalization matches (handles c++, c#, node.js etc.)
        for raw, canonical in NORMALIZE_MAP.items():
            if raw in text_lower:
                skills.add(canonical)

        # Strategy 2: spaCy token matching for single-word skills
        doc = self.nlp(text_lower)

        for token in doc:
            if token.is_stop or token.is_punct:
                continue
            word = token.text.strip()
            if word in TECH_SKILLS:
                if word in SHORT_SKILLS:
                    # Word boundary check for short words
                    pattern = r'\b' + re.escape(word) + r'\b'
                    if re.search(pattern, text_lower):
                        skills.add(word)
                else:
                    skills.add(word)

        # Strategy 3: Noun chunk matching
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.strip()
            if chunk_text in TECH_SKILLS:
                skills.add(chunk_text)

        # Strategy 4: Multi-word skills via substring
        multi_word_skills = {s for s in TECH_SKILLS if " " in s}
        for skill in multi_word_skills:
            if skill in text_lower:
                skills.add(skill)

        result = sorted(skills)
        logger.debug("Extracted {} skills from text ({} chars)", len(result), len(text))
        return result
