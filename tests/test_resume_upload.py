"""
Test resume upload end-to-end + remaining service audits.
Creates a test PDF, uploads it, verifies parsing results.
"""
import sys, os, time, json
os.environ.setdefault("PYTHONPATH", ".")
sys.path.insert(0, ".")

import httpx

BASE = "http://127.0.0.1:8000"
TOKEN = None
PASS = FAIL = 0
ERRORS = []
T = 120  # long timeout for model loading on first upload

def check(name, ok, detail=""):
    global PASS, FAIL, ERRORS
    if ok:
        print(f"  ✓ {name}")
        PASS += 1
    else:
        print(f"  ✗ {name} — {detail}")
        FAIL += 1
        ERRORS.append(f"{name}: {detail}")


def create_test_pdf():
    """Create a minimal test PDF using PyMuPDF."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    text = """Muhammad Ali Khan
ali.khan@example.com
+92 300 1234567

Senior Python Developer | 6+ years of experience

SKILLS:
Python, JavaScript, React, Django, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Redis, Git

EDUCATION:
Bachelor of Science in Computer Science, LUMS 2018

EXPERIENCE:
Lead Backend Engineer at TechFlow (2020-2024)
- Built microservices architecture serving 5M users
- Led team of 4 engineers on payment platform
- Implemented CI/CD pipeline with GitHub Actions

Software Engineer at DataCorp (2018-2020)
- Developed REST APIs with Django and PostgreSQL
- Automated testing with pytest achieving 90% coverage
"""
    page.insert_text((72, 72), text, fontsize=10)
    path = os.path.join(os.path.dirname(__file__), "test_resume.pdf")
    doc.save(path)
    doc.close()
    return path


def test_auth():
    global TOKEN
    print("=== AUTH ===")
    email = f"upload_{int(time.time())}@test.com"
    r = httpx.post(f"{BASE}/api/auth/register",
                   json={"email": email, "password": "testpass123", "full_name": "Ali Khan"}, timeout=T)
    check("Register", r.status_code == 201, f"{r.status_code}")

    r = httpx.post(f"{BASE}/api/auth/token",
                   json={"email": email, "password": "testpass123"}, timeout=T)
    check("Login", r.status_code == 200)
    if r.status_code == 200:
        TOKEN = r.json()["access_token"]


def test_resume_upload(pdf_path):
    print("\n=== RESUME UPLOAD ===")
    if not TOKEN:
        print("  SKIP — no token")
        return

    h = {"Authorization": f"Bearer {TOKEN}"}

    with open(pdf_path, "rb") as f:
        r = httpx.post(
            f"{BASE}/api/resumes/upload",
            headers=h,
            files={"file": ("test_resume.pdf", f, "application/pdf")},
            timeout=T,
        )

    check("Upload 201", r.status_code == 201, f"{r.status_code}: {r.text[:200]}")

    if r.status_code != 201:
        return

    data = r.json()
    check("Has ID", "id" in data)
    check("Has version", data.get("version") == 1)
    check("Has structured_data", "structured_data" in data and data["structured_data"])

    # Parse structured_data
    sd = json.loads(data.get("structured_data", "{}"))
    print(f"  → Parsed: name='{sd.get('name')}', email='{sd.get('email')}', "
          f"phone='{sd.get('phone')}', skills={len(sd.get('skills',[]))} found, "
          f"exp={sd.get('experience_years')}yr")
    print(f"  → Skills: {sd.get('skills', [])}")

    check("Name extracted", sd.get("name", "") != "", f"got: '{sd.get('name')}'")
    check("Email extracted", "ali.khan@example.com" in sd.get("email", ""), f"got: '{sd.get('email')}'")
    check("Phone extracted", "300" in sd.get("phone", ""), f"got: '{sd.get('phone')}'")
    check("Skills ≥ 5", len(sd.get("skills", [])) >= 5, f"got {len(sd.get('skills',[]))}: {sd.get('skills')}")
    check("python in skills", "python" in sd.get("skills", []), str(sd.get("skills")))
    check("Exp ≥ 6", sd.get("experience_years", 0) >= 6, f"got: {sd.get('experience_years')}")

    # Test versioning: upload again
    print("\n=== RESUME VERSIONING ===")
    with open(pdf_path, "rb") as f:
        r2 = httpx.post(
            f"{BASE}/api/resumes/upload",
            headers=h,
            files={"file": ("test_resume_v2.pdf", f, "application/pdf")},
            timeout=T,
        )
    check("Version 2 upload", r2.status_code == 201, f"{r2.status_code}")
    if r2.status_code == 201:
        d2 = r2.json()
        check("Version incremented", d2.get("version") == 2, f"version={d2.get('version')}")
        check("Parent ID set", d2.get("parent_id") == data["id"], f"parent={d2.get('parent_id')}")

    # List resumes
    print("\n=== RESUME LIST ===")
    r3 = httpx.get(f"{BASE}/api/resumes/", headers=h, timeout=T)
    check("List resumes", r3.status_code == 200)
    if r3.status_code == 200:
        items = r3.json().get("items", [])
        check("Has 2 resumes", len(items) == 2, f"got {len(items)}")

    # Get specific resume
    r4 = httpx.get(f"{BASE}/api/resumes/{data['id']}", headers=h, timeout=T)
    check("Get resume by ID", r4.status_code == 200)


def test_auto_apply_service():
    """Audit the auto_apply service for correctness."""
    print("\n=== AUTO_APPLY SERVICE AUDIT ===")
    from app.services.auto_apply import AutoApplyService, DailyLimitReached

    svc = AutoApplyService()
    check("Has daily cap", hasattr(svc, 'settings'), "missing settings")
    check("Has max_applications", hasattr(svc.settings, 'max_applications_per_day'))
    check("DailyLimitReached exists", issubclass(DailyLimitReached, Exception))


def test_scraper_service():
    """Audit scraper service."""
    print("\n=== SCRAPER SERVICE AUDIT ===")
    from app.services.scraper_service import ScraperService
    svc = ScraperService()
    check("ScraperService created", svc is not None)
    check("Has run_all method", hasattr(svc, 'run_all'))
    check("Has store_jobs method", hasattr(svc, 'store_jobs'))


if __name__ == "__main__":
    print("=" * 50)
    print("AutoApply AI — Resume Upload + Service Audit")
    print("=" * 50)

    pdf_path = create_test_pdf()
    print(f"Created test PDF: {pdf_path}\n")

    test_auth()
    test_resume_upload(pdf_path)
    test_auto_apply_service()
    test_scraper_service()

    # Cleanup
    try:
        os.remove(pdf_path)
    except Exception:
        pass

    print(f"\n{'=' * 50}")
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    if ERRORS:
        print("FAILURES:")
        for e in ERRORS:
            print(f"  ✗ {e}")

    sys.exit(1 if FAIL else 0)
