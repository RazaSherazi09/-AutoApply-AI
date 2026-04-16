import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api"

def print_step(msg):
    print(f"\n--- {msg} ---")

def run_tests():
    session = requests.Session()
    
    email = f"qa_test_{int(time.time())}@example.com"
    password = "password123"
    
    # 1. Register
    print_step("Testing Registration")
    res = session.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "QA Tester"
    })
    print("Register response:", res.status_code, res.text)
    
    # 2. Register duplicate (Edge Case)
    print_step("Testing Duplicate Registration")
    res_dup = session.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "QA Tester Dup"
    })
    print("Duplicate register response:", res_dup.status_code, res_dup.text)
    
    # 3. Login
    print_step("Testing Login")
    res_login = session.post(f"{BASE_URL}/auth/token", json={
        "email": email,
        "password": password
    })
    print("Login response:", res_login.status_code, res_login.text)
    
    if res_login.status_code != 200:
        print("Login failed, aborting rest of API tests")
        return
        
    token = res_login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    session.headers.update(headers)
    
    # 4. Settings/Preferences
    print_step("Testing Settings & Preferences")
    res_pref = session.get(f"{BASE_URL}/settings/preferences")
    print("Get Prefs:", res_pref.status_code, res_pref.text)
    
    res_pref_update = session.put(f"{BASE_URL}/settings/preferences", json={
        "desired_titles": ["Engineer", "Tester"],
        "desired_locations": ["Remote"],
        "excluded_companies": ["EvilCorp"],
        "min_salary": 80000,
        "remote_only": True,
        "country": "US",
        "workplace_type": "Remote"
    })
    print("Update Prefs:", res_pref_update.status_code, res_pref_update.text)
    
    # 5. Empty Resume State & Upload logic
    print_step("Testing Resumes (Empty state)")
    res_res = session.get(f"{BASE_URL}/resumes/")
    print("Get Resumes:", res_res.status_code, res_res.text)
    
    # 6. Job Scrape (No Resume Edge Case)
    print_step("Testing Job Scrape without Resume")
    res_scrape = session.post(f"{BASE_URL}/jobs/scrape", json={"query": "auto", "location": "auto"})
    print("Scrape response (should maybe err or skip matching):", res_scrape.status_code, res_scrape.text)

    # 7. Matches (Empty)
    print_step("Testing Matches")
    res_match = session.get(f"{BASE_URL}/matches/")
    print("Matches response:", res_match.status_code, res_match.text)

if __name__ == "__main__":
    run_tests()
