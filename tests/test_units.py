"""Unit tests for services — runs locally, loads models once."""
import sys, os
os.environ.setdefault("PYTHONPATH", ".")
sys.path.insert(0, ".")

PASS = FAIL = 0
ERRORS = []

def check(name, ok, detail=""):
    global PASS, FAIL, ERRORS
    if ok:
        print(f"  ✓ {name}")
        PASS += 1
    else:
        print(f"  ✗ {name} — {detail}")
        FAIL += 1
        ERRORS.append(f"{name}: {detail}")

def test_skill_extractor():
    print("=== SKILL EXTRACTOR ===")
    from app.services.job_skill_extractor import JobSkillExtractor
    ext = JobSkillExtractor()

    s = ext.extract("Python developer with React, Node.js, AWS, PostgreSQL, Docker")
    check("python", "python" in s, str(s))
    check("react", "react" in s, str(s))
    check("nodejs", "nodejs" in s, str(s))
    check("aws", "aws" in s, str(s))
    check("docker", "docker" in s, str(s))

    s2 = ext.extract("C++ and C# developer, TypeScript, .NET")
    check("cpp", "cpp" in s2, str(s2))
    check("csharp", "csharp" in s2, str(s2))
    check("typescript", "typescript" in s2, str(s2))

def test_resume_parser():
    print("\n=== RESUME PARSER ===")
    from app.services.resume_parser import ResumeParser
    parser = ResumeParser.get_instance()

    text = """John Smith
john.smith@email.com
+1 (555) 123-4567

Senior Python Developer with 8+ years of experience building scalable backend systems.

Skills: Python, JavaScript, React, Django, FastAPI, Docker, Kubernetes, AWS, PostgreSQL

Education:
Bachelor of Science in Computer Science from MIT, 2015
"""
    ent = parser.extract_entities(text)
    check("Name", ent["name"] == "John Smith", f"'{ent['name']}'")
    check("Email", ent["email"] == "john.smith@email.com", f"'{ent['email']}'")
    check("Phone has 555", "555" in ent["phone"], f"'{ent['phone']}'")
    check("Skills ≥ 5", len(ent["skills"]) >= 5, f"{len(ent['skills'])}: {ent['skills']}")
    check("python in skills", "python" in ent["skills"])
    check("react in skills", "react" in ent["skills"])
    check("docker in skills", "docker" in ent["skills"])
    check("Exp ≥ 8", ent["experience_years"] >= 8, f"{ent['experience_years']}")

    # Minimal
    m = parser.extract_entities("Jane Doe\njane@x.org\nPython and Java developer")
    check("Min: name", m["name"] != "", f"'{m['name']}'")
    check("Min: email", m["email"] == "jane@x.org")
    check("Min: python", "python" in m["skills"])
    check("Min: java", "java" in m["skills"])

def test_matcher():
    print("\n=== MATCHER ===")
    from app.services.matcher import MatcherService
    svc = MatcherService()

    check("Title match > 0.5", svc._compute_title_score(["Python Dev"], "Senior Python Dev") > 0.5)
    check("No title pref = 0.5", svc._compute_title_score([], "Any") == 0.5)
    check("Location exact = 1.0", svc._compute_location_score(["New York"], "New York, NY", False) == 1.0)
    check("Remote + only = 1.0", svc._compute_location_score([], "Remote", True) == 1.0)
    check("Non-remote + only = 0.0", svc._compute_location_score([], "SF", True) == 0.0)
    check("Skill overlap > 0", svc._compute_skill_score({"python","react"}, {"python","django"}) > 0)
    check("Empty skills = 0", svc._compute_skill_score(set(), set()) == 0.0)

def test_embedding():
    print("\n=== EMBEDDING ===")
    from app.services.embedding import EmbeddingService
    import numpy as np

    svc = EmbeddingService.get_instance()
    vec = svc.encode("Python developer")
    check("ndarray", isinstance(vec, np.ndarray))
    check("dim=384", vec.shape == (384,), f"{vec.shape}")

    bts = EmbeddingService.to_bytes(vec)
    check("bytes type", isinstance(bts, bytes))
    check("len=1536", len(bts) == 384 * 4)

    restored = EmbeddingService.from_bytes(bts)
    check("roundtrip", np.allclose(vec, restored))

    check("self-sim ≈ 1.0", abs(EmbeddingService.cosine_similarity(vec, vec) - 1.0) < 0.01)

    vec2 = svc.encode("gardening roses flowers")
    check("unrelated < 0.5", EmbeddingService.cosine_similarity(vec, vec2) < 0.5)

def test_daily_limit():
    print("\n=== DAILY LIMIT ===")
    from app.services.auto_apply import AutoApplyService, DailyLimitReached
    check("Exception class", issubclass(DailyLimitReached, Exception))
    check("Service created", AutoApplyService() is not None)

if __name__ == "__main__":
    print("="*50)
    print("AutoApply AI — Unit Tests")
    print("="*50)
    test_skill_extractor()
    test_resume_parser()
    test_matcher()
    test_embedding()
    test_daily_limit()
    print(f"\n{'='*50}\nRESULTS: {PASS} passed, {FAIL} failed")
    if ERRORS:
        print("FAILURES:")
        for e in ERRORS: print(f"  ✗ {e}")
    sys.exit(1 if FAIL else 0)
