import requests
import json
import uuid
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def print_step(step_num, title):
    print(f"\n{'='*50}")
    print(f"STEP {step_num} — {title}")
    print(f"{'='*50}")

def run_tests():
    # Setup test user
    uid = str(uuid.uuid4())[:8]
    email = f"test_{uid}@example.com"
    password = "SuperSecretPassword123!"
    
    print_step(1, "USER AUTHENTICATION FLOW")
    # 1. Register
    reg_res = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "full_name": f"Test User {uid}"
    })
    
    if reg_res.status_code == 201:
        print("[SUCCESS] User registration successful.")
    else:
        print(f"[FAILED] User registration: {reg_res.text}")
        sys.exit(1)

    # 2. Login
    login_res = requests.post(f"{BASE_URL}/auth/token", json={
        "email": email,
        "password": password
    })
    
    if login_res.status_code == 200:
        token = login_res.json().get("access_token")
        print("[SUCCESS] Login successful. JWT Token received.")
    else:
        print(f"[FAILED] Login: {login_res.text}")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    print_step(3, "USER PREFERENCES SYSTEM") # Doing this before upload might be better, or after.
    # 3. Preferences
    pref_res = requests.put(f"{BASE_URL}/settings/preferences", headers=headers, json={
        "desired_titles": ["Software Engineer", "Backend Developer", "Developer"],
        "desired_locations": ["Remote", "New York"],
        "min_salary": 80000,
        "remote_only": False,
        "excluded_companies": ["BadCorp"]
    })
    if pref_res.status_code == 200:
        print("[SUCCESS] User preferences saved successfully.")
    else:
        print(f"[FAILED] User preferences: {pref_res.status_code} {pref_res.text}")

    print_step(2, "RESUME UPLOAD SYSTEM")
    # 3. Create dummy PDF & Upload
    with open("test_e2e.pdf", "wb") as f:
        f.write(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")
    
    up_res = requests.post(f"{BASE_URL}/resumes/upload", headers=headers, files={
        "file": ("test_e2e.pdf", open("test_e2e.pdf", "rb"), "application/pdf")
    })
    
    resume_id = None
    if up_res.status_code == 201:
        data = up_res.json()
        resume_id = data.get("id")
        parsed = json.loads(data.get("structured_data", "{}"))
        print(f"[SUCCESS] Resume uploaded! ID: {resume_id}")
        print(f"  -> Extracted Skills Count: {len(parsed.get('skills', []))}")
    else:
        print(f"[FAILED] Resume upload: {up_res.status_code} {up_res.text}")

    print_step(5, "JOB SCRAPING SYSTEM")
    # Trigger scrape
    print("Triggering background scrape. Waiting for completion...")
    scrape_res = requests.post(f"{BASE_URL}/jobs/scrape", headers=headers, json={"query": "Software Engineer", "location": "Remote"})
    if scrape_res.status_code in [200, 202]:
        print("[SUCCESS] Job scraping triggered successfully.")
        # Some endpoints return 202 and run in background. If so, let's just query jobs list.
    else:
        print(f"[FAILED] Job scrape: {scrape_res.status_code} {scrape_res.text}")
        
    print("Fetching global jobs list...")
    jobs_res = requests.get(f"{BASE_URL}/jobs/", headers=headers, params={"limit": 5})
    if jobs_res.status_code == 200:
        jobs = jobs_res.json().get("items", [])
        print(f"[SUCCESS] Total jobs returned: {len(jobs)}")
        if jobs:
            print(f"  -> Sample job: {jobs[0].get('title')} at {jobs[0].get('company')}")
    else:
        print(f"[FAILED] Fetch jobs: {jobs_res.status_code} {jobs_res.text}")

    print_step(6, "MATCHING ENGINE")
    # Matches endpoint implicitly triggers matcher for un-matched jobs? Or just fetches?
    # Usually `GET /api/matches/` just fetches, maybe there's a POST to trigger.
    # Let's check `GET /matches/`
    print("Fetching computed matches for user...")
    match_res = requests.get(f"{BASE_URL}/matches/", headers=headers, params={"limit": 10})
    if match_res.status_code == 200:
        matches = match_res.json().get("items", [])
        print(f"[SUCCESS] Total matches via API: {match_res.json().get('total')}")
        if matches:
            m = matches[0]
            print(f"  -> Match #1 Score: {m.get('final_score')} for {m.get('job', {}).get('title')}")
    else:
        print(f"[FAILED] Fetch matches: {match_res.status_code} {match_res.text}")
        
    print_step(4, "DELETE / UPDATE USER DATA")
    if resume_id:
        del_res = requests.post(f"{BASE_URL}/resumes/{resume_id}/delete", headers=headers)
        if del_res.status_code == 200:
            print("[SUCCESS] Resume deleted successfully.")
        else:
            print(f"[FAILED] Resume deletion: {del_res.status_code} {del_res.text}")

    print("\n[DONE] E2E Integration test complete.")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"Test crashed: {e}")
