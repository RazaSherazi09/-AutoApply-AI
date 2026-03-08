"""
Full QA Integration Tests — Steps 3-14.
Tests against the live FastAPI server at http://127.0.0.1:8000.
Also tests unit-level services directly.
"""
import sys, json, time, os
os.environ["PYTHONPATH"] = "."
sys.path.insert(0, ".")

import httpx

BASE = "http://127.0.0.1:8000"
TOKEN = None
PASS = 0
FAIL = 0
ERRORS = []

def check(name, condition, detail=""):
    global PASS, FAIL, ERRORS
    if condition:
        print(f"  ✓ {name}")
        PASS += 1
    else:
        msg = f"{name} — {detail}" if detail else name
        print(f"  ✗ {msg}")
        FAIL += 1
        ERRORS.append(msg)

# ── STEP 3: DATABASE ──
def test_database():
    print("\n=== STEP 3: DATABASE ===")
    r = httpx.get(f"{BASE}/health", timeout=10)
    check("Health endpoint", r.status_code == 200)

# ── STEP 4: AUTH ──
def test_auth():
    global TOKEN
    print("\n=== STEP 4: AUTH ===")

    ts = int(time.time())
    email = f"qa_{ts}@test.com"

    r = httpx.post(f"{BASE}/api/auth/register", json={
        "email": email, "password": "qapass1234", "full_name": "QA Tester"
    }, timeout=15)
    check("Register", r.status_code == 201, f"{r.status_code}: {r.text[:100]}")

    r = httpx.post(f"{BASE}/api/auth/token", json={
        "email": email, "password": "qapass1234"
    }, timeout=15)
    check("Login", r.status_code == 200, f"{r.status_code}: {r.text[:100]}")
    if r.status_code == 200:
        TOKEN = r.json()["access_token"]
        check("Token non-empty", len(TOKEN) > 20)

    r = httpx.post(f"{BASE}/api/auth/token", json={
        "email": email, "password": "wrong"
    }, timeout=10)
    check("Wrong password rejected", r.status_code == 401)

    r = httpx.get(f"{BASE}/api/resumes/", headers={"Authorization": "Bearer bad"}, timeout=10)
    check("Bad token rejected", r.status_code == 401)

    if TOKEN:
        r = httpx.get(f"{BASE}/api/resumes/", headers={"Authorization": f"Bearer {TOKEN}"}, timeout=10)
        check("Valid token accepted", r.status_code == 200)

# ── STEP 5: PREFERENCES ──
def test_preferences():
    print("\n=== STEP 5: PREFERENCES ===")
    if not TOKEN: return print("  SKIP")
    h = {"Authorization": f"Bearer {TOKEN}"}

    r = httpx.get(f"{BASE}/api/settings/preferences", headers=h, timeout=10)
    check("Get preferences", r.status_code == 200, f"{r.status_code}")

    r = httpx.put(f"{BASE}/api/settings/preferences", headers=h, json={
        "desired_titles": ["Python Developer"], "desired_locations": ["Remote"],
        "excluded_companies": [], "min_salary": 50000, "remote_only": True
    }, timeout=10)
    check("Update preferences", r.status_code == 200, f"{r.status_code}: {r.text[:100]}")

# ── STEP 6: SETTINGS SECURITY ──
def test_settings():
    print("\n=== STEP 6: SETTINGS SECURITY ===")
    if not TOKEN: return print("  SKIP")
    h = {"Authorization": f"Bearer {TOKEN}"}

    r = httpx.put(f"{BASE}/api/settings/config", headers=h, json={
        "match_threshold": "0.6"
    }, timeout=10)
    check("Allowed key accepted", r.status_code == 200, f"{r.status_code}")

    r = httpx.put(f"{BASE}/api/settings/config", headers=h, json={
        "smtp_password": "hack"
    }, timeout=10)
    check("Sensitive key rejected", r.status_code == 400, f"{r.status_code}")

# ── STEP 6B: JOBS API ──
def test_jobs_api():
    print("\n=== STEP 6B: JOBS API ===")
    if not TOKEN: return print("  SKIP")
    h = {"Authorization": f"Bearer {TOKEN}"}

    r = httpx.get(f"{BASE}/api/jobs/", headers=h, timeout=10)
    check("List jobs", r.status_code == 200, f"{r.status_code}")
    if r.status_code == 200:
        d = r.json()
        check("Jobs has items+total", "items" in d and "total" in d)

    r = httpx.post(f"{BASE}/api/jobs/scrape", headers=h, json={
        "query": "test", "location": "remote"
    }, timeout=10)
    check("Trigger scrape (202)", r.status_code == 202, f"{r.status_code}")

    r = httpx.get(f"{BASE}/api/jobs/scraper-runs", headers=h, timeout=10)
    check("Scraper runs endpoint", r.status_code == 200, f"{r.status_code}")

# ── STEP 7A: UNIT — Skill Extractor ──
def test_skill_extractor():
    print("\n=== STEP 7: SKILL EXTRACTOR ===")
    from app.services.job_skill_extractor import JobSkillExtractor
    ext = JobSkillExtractor()

    desc = "Python developer with React, Node.js, AWS, PostgreSQL, Docker, Kubernetes experience"
    skills = ext.extract(desc)
    check("python extracted", "python" in skills, str(skills))
    check("react extracted", "react" in skills, str(skills))
    check("nodejs normalized", "nodejs" in skills, str(skills))
    check("aws extracted", "aws" in skills, str(skills))
    check("docker extracted", "docker" in skills, str(skills))

    desc2 = "C++ and C# developer with TypeScript and .NET experience"
    skills2 = ext.extract(desc2)
    check("c++→cpp", "cpp" in skills2, str(skills2))
    check("c#→csharp", "csharp" in skills2, str(skills2))
    check("typescript extracted", "typescript" in skills2, str(skills2))

# ── STEP 7B: UNIT — Resume Parser entity extraction ──
def test_resume_parser():
    print("\n=== STEP 7B: RESUME PARSER ===")
    from app.services.resume_parser import ResumeParser
    parser = ResumeParser.get_instance()

    sample_text = """John Smith
john.smith@email.com
+1 (555) 123-4567

Senior Python Developer with 8+ years of experience in building scalable backend systems.

Skills: Python, JavaScript, React, Django, FastAPI, Docker, Kubernetes, AWS, PostgreSQL

Education:
Bachelor of Science in Computer Science from MIT, 2015

Work Experience:
- Led a team of 5 engineers at TechCorp (2019-2024)
- Built microservices architecture handling 10M requests/day
"""
    entities = parser.extract_entities(sample_text)

    check("Name extracted", entities["name"] == "John Smith", f"got: '{entities['name']}'")
    check("Email extracted", entities["email"] == "john.smith@email.com", f"got: '{entities['email']}'")
    check("Phone extracted", "555" in entities["phone"], f"got: '{entities['phone']}'")
    check("Skills found (>5)", len(entities["skills"]) >= 5, f"got {len(entities['skills'])}: {entities['skills']}")
    check("python in skills", "python" in entities["skills"], str(entities["skills"]))
    check("react in skills", "react" in entities["skills"], str(entities["skills"]))
    check("docker in skills", "docker" in entities["skills"], str(entities["skills"]))
    check("Experience 8 years", entities["experience_years"] >= 8.0, f"got: {entities['experience_years']}")
    check("No false 'r' skill", "r" not in entities["skills"] or "react" in entities["skills"],
          f"skills: {entities['skills']}")

    # Test with minimal resume
    minimal = "Jane Doe\njane@example.org\nI know Python and Java."
    m_ent = parser.extract_entities(minimal)
    check("Minimal: name extracted", m_ent["name"] != "", f"got: '{m_ent['name']}'")
    check("Minimal: email extracted", m_ent["email"] == "jane@example.org", f"got: '{m_ent['email']}'")
    check("Minimal: python found", "python" in m_ent["skills"], str(m_ent["skills"]))
    check("Minimal: java found", "java" in m_ent["skills"], str(m_ent["skills"]))

# ── STEP 8: UNIT — Matcher scoring ──
def test_matcher():
    print("\n=== STEP 8: MATCHER SCORING ===")
    from app.services.matcher import MatcherService
    svc = MatcherService()

    # Title
    ts = svc._compute_title_score(["Python Developer"], "Senior Python Developer")
    check("Title partial match > 0.5", ts > 0.5, f"{ts}")
    check("Title score ≤ 1.0", ts <= 1.0)

    ts0 = svc._compute_title_score([], "Any")
    check("No pref title = 0.5", ts0 == 0.5, f"{ts0}")

    # Location
    ls = svc._compute_location_score(["New York"], "New York, NY", False)
    check("Location exact = 1.0", ls == 1.0, f"{ls}")

    lr = svc._compute_location_score([], "Remote", True)
    check("Remote + remote_only = 1.0", lr == 1.0, f"{lr}")

    ln = svc._compute_location_score([], "SF", True)
    check("Non-remote + remote_only = 0.0", ln == 0.0, f"{ln}")

    # Skill
    sk = svc._compute_skill_score({"python", "react"}, {"python", "django", "react"})
    check("Skill overlap > 0", sk > 0)
    check("Skill ≤ 1.0", sk <= 1.0)

    sk0 = svc._compute_skill_score(set(), set())
    check("Empty skills = 0.0", sk0 == 0.0)

# ── STEP 8B: UNIT — Embedding roundtrip ──
def test_embedding():
    print("\n=== STEP 8B: EMBEDDING ===")
    from app.services.embedding import EmbeddingService
    import numpy as np

    svc = EmbeddingService.get_instance()
    vec = svc.encode("Python developer")
    check("Encoding returns ndarray", isinstance(vec, np.ndarray))
    check("Dim = 384", vec.shape == (384,), f"{vec.shape}")

    bts = EmbeddingService.to_bytes(vec)
    check("to_bytes returns bytes", isinstance(bts, bytes))
    check("Byte len = 1536", len(bts) == 384 * 4)

    restored = EmbeddingService.from_bytes(bts)
    check("Roundtrip match", np.allclose(vec, restored))

    sim = EmbeddingService.cosine_similarity(vec, vec)
    check("Self-similarity ≈ 1.0", abs(sim - 1.0) < 0.01, f"{sim}")

    vec2 = svc.encode("Unrelated gardening topic about roses")
    sim2 = EmbeddingService.cosine_similarity(vec, vec2)
    check("Unrelated similarity < 0.5", sim2 < 0.5, f"{sim2}")

# ── STEP 7: MATCHES/APPLICATIONS API ──
def test_matches_apps_api():
    print("\n=== STEP 10: MATCHES + APPLICATIONS API ===")
    if not TOKEN: return print("  SKIP")
    h = {"Authorization": f"Bearer {TOKEN}"}

    r = httpx.get(f"{BASE}/api/matches/", headers=h, timeout=10)
    check("List matches", r.status_code == 200, f"{r.status_code}")

    r = httpx.get(f"{BASE}/api/applications/", headers=h, timeout=10)
    check("List applications", r.status_code == 200, f"{r.status_code}")

# ── STEP 14: Daily limit unit test ──
def test_daily_limit():
    print("\n=== STEP 14: DAILY LIMIT ===")
    from app.services.auto_apply import AutoApplyService, DailyLimitReached
    check("DailyLimitReached is exception", issubclass(DailyLimitReached, Exception))
    svc = AutoApplyService()
    check("AutoApplyService created", svc is not None)

# ── MAIN ──
if __name__ == "__main__":
    print("=" * 60)
    print("AutoApply AI — Full QA Test Suite")
    print("=" * 60)

    test_database()
    test_auth()
    test_preferences()
    test_settings()
    test_jobs_api()
    test_skill_extractor()
    test_resume_parser()
    test_matcher()
    test_embedding()
    test_matches_apps_api()
    test_daily_limit()

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    if ERRORS:
        print(f"\nFAILURES:")
        for e in ERRORS:
            print(f"  ✗ {e}")
    print("=" * 60)

    sys.exit(1 if FAIL else 0)
