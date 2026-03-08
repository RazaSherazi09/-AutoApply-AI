"""API-level tests only — no model loading required. Fast."""
import sys, time
import httpx

BASE = "http://127.0.0.1:8000"
TOKEN = None
PASS = FAIL = 0
ERRORS = []
T = 30  # timeout seconds (first request may trigger model load)

def check(name, ok, detail=""):
    global PASS, FAIL, ERRORS
    if ok:
        print(f"  ✓ {name}")
        PASS += 1
    else:
        print(f"  ✗ {name} — {detail}")
        FAIL += 1
        ERRORS.append(f"{name}: {detail}")

def run():
    global TOKEN
    print("=== HEALTH ===")
    check("Health", httpx.get(f"{BASE}/health", timeout=T).status_code == 200)

    print("\n=== AUTH ===")
    email = f"qa{int(time.time())}@t.com"
    r = httpx.post(f"{BASE}/api/auth/register", json={"email":email,"password":"qapass123","full_name":"QA"}, timeout=T)
    check("Register", r.status_code == 201, f"{r.status_code}:{r.text[:80]}")

    r = httpx.post(f"{BASE}/api/auth/token", json={"email":email,"password":"qapass123"}, timeout=T)
    check("Login", r.status_code == 200, f"{r.status_code}:{r.text[:80]}")
    if r.status_code == 200: TOKEN = r.json()["access_token"]

    check("Bad pw rejected", httpx.post(f"{BASE}/api/auth/token", json={"email":email,"password":"x"}, timeout=T).status_code == 401)
    check("Bad token", httpx.get(f"{BASE}/api/resumes/", headers={"Authorization":"Bearer x"}, timeout=T).status_code == 401)

    if not TOKEN:
        print("ABORT — no token"); return

    h = {"Authorization": f"Bearer {TOKEN}"}

    print("\n=== PREFERENCES ===")
    check("Get prefs", httpx.get(f"{BASE}/api/settings/preferences", headers=h, timeout=T).status_code == 200)
    r = httpx.put(f"{BASE}/api/settings/preferences", headers=h, json={
        "desired_titles":["Dev"],"desired_locations":["Remote"],"excluded_companies":[],"min_salary":0,"remote_only":True
    }, timeout=T)
    check("Update prefs", r.status_code == 200, f"{r.status_code}")

    print("\n=== SETTINGS ===")
    check("Update setting", httpx.put(f"{BASE}/api/settings/config", headers=h, json={"match_threshold":"0.6"}, timeout=T).status_code == 200)
    check("Block sensitive", httpx.put(f"{BASE}/api/settings/config", headers=h, json={"smtp_password":"hack"}, timeout=T).status_code == 400)

    print("\n=== JOBS ===")
    r = httpx.get(f"{BASE}/api/jobs/", headers=h, timeout=T)
    check("List jobs", r.status_code == 200)
    check("Scrape trigger", httpx.post(f"{BASE}/api/jobs/scrape", headers=h, json={"query":"python","location":"remote"}, timeout=T).status_code == 202)
    check("Scraper runs", httpx.get(f"{BASE}/api/jobs/scraper-runs", headers=h, timeout=T).status_code == 200)

    print("\n=== MATCHES ===")
    check("List matches", httpx.get(f"{BASE}/api/matches/", headers=h, timeout=T).status_code == 200)

    print("\n=== APPLICATIONS ===")
    check("List apps", httpx.get(f"{BASE}/api/applications/", headers=h, timeout=T).status_code == 200)

    print(f"\n{'='*50}\nRESULTS: {PASS} passed, {FAIL} failed")
    if ERRORS:
        print("FAILURES:")
        for e in ERRORS: print(f"  ✗ {e}")

if __name__ == "__main__":
    run()
    sys.exit(1 if FAIL else 0)
