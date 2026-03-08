"""
AutoApply AI — Streamlit Dashboard.

All data flows through FastAPI via httpx. No direct DB imports.
Run: streamlit run app/frontend/streamlit_app.py
"""

from __future__ import annotations

import json

import httpx
import streamlit as st

API_BASE = "http://localhost:8000"


# ── HTTP helpers ──

def api_get(endpoint: str, token: str) -> dict | list | None:
    """Authenticated GET request to the API."""
    try:
        resp = httpx.get(
            f"{API_BASE}{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()
        st.error(f"API Error: {resp.status_code} — {resp.text}")
    except httpx.ConnectError:
        st.error("❌ Cannot connect to API. Is the backend running?")
    return None


def api_post(endpoint: str, token: str, data: dict | None = None, files: dict | None = None) -> dict | None:
    """Authenticated POST request to the API."""
    try:
        kwargs: dict = {
            "headers": {"Authorization": f"Bearer {token}"},
            "timeout": 60,
        }
        if files:
            kwargs["files"] = files
        elif data is not None:
            kwargs["json"] = data
            kwargs["headers"]["Content-Type"] = "application/json"

        resp = httpx.post(f"{API_BASE}{endpoint}", **kwargs)
        if resp.status_code in (200, 201, 202):
            return resp.json()
        st.error(f"API Error: {resp.status_code} — {resp.text}")
    except httpx.ConnectError:
        st.error("❌ Cannot connect to API. Is the backend running?")
    return None


def api_put(endpoint: str, token: str, data: dict) -> dict | None:
    """Authenticated PUT request to the API."""
    try:
        resp = httpx.put(
            f"{API_BASE}{endpoint}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=data,
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()
        st.error(f"API Error: {resp.status_code} — {resp.text}")
    except httpx.ConnectError:
        st.error("❌ Cannot connect to API. Is the backend running?")
    return None


# ── Session state init ──

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None


# ── Page config ──

st.set_page_config(
    page_title="AutoApply AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Auth pages ──

def login_page() -> None:
    """Login / Registration page."""
    st.title("🎯 AutoApply AI")
    st.caption("Local-first intelligent job application agent")

    tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted and email and password:
            try:
                resp = httpx.post(
                    f"{API_BASE}/api/auth/token",
                    json={"email": email, "password": password},
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.user = {"email": email}
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            except httpx.ConnectError:
                st.error("❌ Cannot connect to API")

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("Full Name", key="reg_name")
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password", type="password", key="reg_password")
            submitted = st.form_submit_button("Register", use_container_width=True)

        if submitted and name and email and password:
            try:
                resp = httpx.post(
                    f"{API_BASE}/api/auth/register",
                    json={"email": email, "password": password, "full_name": name},
                    timeout=15,
                )
                if resp.status_code == 201:
                    st.success("✅ Account created! Please login.")
                else:
                    st.error(f"Registration failed: {resp.text}")
            except httpx.ConnectError:
                st.error("❌ Cannot connect to API")


# ── Dashboard ──

def dashboard_page(token: str) -> None:
    """Main dashboard with stats overview."""
    st.title("📊 Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    # Jobs count
    jobs = api_get("/api/jobs/?limit=1", token)
    with col1:
        st.metric("Total Jobs", jobs.get("total", 0) if jobs else 0)

    # Pending matches
    matches = api_get("/api/matches/?status_filter=PENDING_APPROVAL&limit=1", token)
    with col2:
        st.metric("Pending Matches", matches.get("total", 0) if matches else 0)

    # Applications
    apps = api_get("/api/applications/?limit=1", token)
    with col3:
        st.metric("Applications", apps.get("total", 0) if apps else 0)

    # Resumes
    resumes = api_get("/api/resumes/?limit=1", token)
    with col4:
        st.metric("Resumes", resumes.get("total", 0) if resumes else 0)

    # Scraper health
    st.subheader("🔍 Recent Scraper Runs")
    runs = api_get("/api/jobs/scraper-runs?limit=10", token)
    if runs:
        for run in runs:
            status_emoji = "✅" if run["status"] == "SUCCESS" else "❌"
            st.text(
                f"{status_emoji} {run['provider']} | "
                f"Found: {run['jobs_found']} | New: {run['jobs_new']} | "
                f"Duration: {run['duration_seconds']:.1f}s | "
                f"{run['started_at']}"
            )


# ── Resume pages ──

def resume_page(token: str) -> None:
    """Resume upload and management."""
    st.title("📄 Resumes")

    # Upload
    st.subheader("Upload Resume (PDF)")
    uploaded = st.file_uploader("Choose PDF", type=["pdf"])
    if uploaded and st.button("Upload & Parse"):
        result = api_post(
            "/api/resumes/upload",
            token,
            files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
        )
        if result:
            st.success(f"✅ Resume v{result.get('version', 1)} uploaded and parsed!")
            data = json.loads(result.get("structured_data", "{}"))
            st.json(data)

    st.divider()

    # List
    st.subheader("Your Resumes")
    resumes = api_get("/api/resumes/", token)
    if resumes and resumes.get("items"):
        for r in resumes["items"]:
            with st.expander(f"📄 {r['file_name']} (v{r['version']})"):
                data = json.loads(r.get("structured_data", "{}"))
                st.write(f"**Name:** {data.get('name', 'N/A')}")
                st.write(f"**Email:** {data.get('email', 'N/A')}")
                st.write(f"**Phone:** {data.get('phone', 'N/A')}")
                st.write(f"**Experience:** {data.get('experience_years', 0)} years")
                st.write(f"**Skills:** {', '.join(data.get('skills', []))}")
    else:
        st.info("No resumes uploaded yet")


# ── Jobs page ──

def jobs_page(token: str) -> None:
    """Browse scraped job listings."""
    st.title("💼 Job Listings")

    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("Search", placeholder="e.g. Python Developer")
    with col2:
        source = st.selectbox("Source", ["All", "adzuna", "greenhouse", "lever", "workday"])
    with col3:
        remote = st.checkbox("Remote only")

    params = f"?limit=50&remote_only={remote}"
    if search:
        params += f"&search={search}"
    if source != "All":
        params += f"&source={source}"

    jobs = api_get(f"/api/jobs/{params}", token)
    if jobs and jobs.get("items"):
        st.caption(f"Showing {len(jobs['items'])} of {jobs['total']} jobs")
        for job in jobs["items"]:
            with st.expander(f"**{job['title']}** — {job['company']} ({job['location']})"):
                st.write(f"**Source:** {job['source']} | **Type:** {job['job_type']} | **Level:** {job['experience_level']} | **Remote:** {job['remote_status']}")
                if job.get("salary_min") or job.get("salary_max"):
                    st.write(f"💰 ${job.get('salary_min', '?')} - ${job.get('salary_max', '?')}")
                skills = json.loads(job.get("extracted_skills", "[]"))
                if skills:
                    st.write(f"**Skills:** {', '.join(skills)}")
                st.write(job.get("description", "")[:500])
                st.link_button("Apply ↗", job["url"])
    else:
        st.info("No jobs found")

    # Manual scrape trigger
    st.divider()
    st.subheader("🔄 Trigger Manual Scrape")
    col1, col2 = st.columns(2)
    with col1:
        scrape_query = st.text_input("Query", "software engineer", key="scrape_q")
    with col2:
        scrape_loc = st.text_input("Location", "remote", key="scrape_l")
    if st.button("Start Scraping"):
        result = api_post("/api/jobs/scrape", token, {"query": scrape_query, "location": scrape_loc})
        if result:
            st.success("🔄 Scrape started in the background!")


# ── Matches page ──

def matches_page(token: str) -> None:
    """Review and approve/reject job matches."""
    st.title("🎯 Pending Matches")

    status_filter = st.selectbox("Filter", ["PENDING_APPROVAL", "APPROVED", "REJECTED", "All"])
    params = "?limit=50"
    if status_filter != "All":
        params += f"&status_filter={status_filter}"

    matches = api_get(f"/api/matches/{params}", token)
    if matches and matches.get("items"):
        st.caption(f"{len(matches['items'])} of {matches['total']} matches")

        for m in matches["items"]:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{m.get('job_title', 'N/A')}** — {m.get('job_company', 'N/A')}")
                    st.caption(
                        f"Score: **{m['final_score']:.2f}** | "
                        f"Semantic: {m['semantic_score']:.2f} | "
                        f"Skills: {m['skill_score']:.2f} | "
                        f"Title: {m['title_score']:.2f} | "
                        f"Location: {m['location_score']:.2f}"
                    )
                with col2:
                    if m["status"] == "PENDING_APPROVAL":
                        if st.button("✅ Approve", key=f"approve_{m['id']}"):
                            api_post(f"/api/matches/{m['id']}/approve", token)
                            st.rerun()
                with col3:
                    if m["status"] == "PENDING_APPROVAL":
                        if st.button("❌ Reject", key=f"reject_{m['id']}"):
                            api_post(f"/api/matches/{m['id']}/reject", token)
                            st.rerun()
    else:
        st.info("No matches found")


# ── Applications page ──

def applications_page(token: str) -> None:
    """Track application status and retry failed ones."""
    st.title("📋 Applications")

    apps = api_get("/api/applications/?limit=50", token)
    if apps and apps.get("items"):
        for app in apps["items"]:
            status_emoji = {
                "PENDING": "⏳", "SENT": "📨", "SUBMITTED": "✅",
                "FAILED": "❌", "MANUAL_REVIEW": "👀"
            }.get(app["status"], "❓")

            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{status_emoji} **Match #{app['match_id']}** — {app['handler_type']} via {app['method']}")
                    st.caption(
                        f"Status: {app['status']} | "
                        f"Retries: {app['retry_count']}/{app['max_retries']}"
                    )
                    if app.get("error_log"):
                        st.error(app["error_log"])
                with col2:
                    if app["status"] in ("FAILED", "MANUAL_REVIEW"):
                        if st.button("🔄 Retry", key=f"retry_{app['id']}"):
                            api_post(f"/api/applications/{app['id']}/retry", token)
                            st.rerun()
    else:
        st.info("No applications yet")


# ── Preferences page ──

def preferences_page(token: str) -> None:
    """Manage job search preferences."""
    st.title("⚙️ Preferences")

    pref = api_get("/api/settings/preferences", token)

    if pref:
        titles = json.loads(pref.get("desired_titles", "[]"))
        locations = json.loads(pref.get("desired_locations", "[]"))
        excluded = json.loads(pref.get("excluded_companies", "[]"))

        with st.form("pref_form"):
            st.subheader("Job Search Criteria")
            titles_input = st.text_area(
                "Desired Titles (one per line)",
                "\n".join(titles),
            )
            locations_input = st.text_area(
                "Desired Locations (one per line)",
                "\n".join(locations),
            )
            excluded_input = st.text_area(
                "Excluded Companies (one per line)",
                "\n".join(excluded),
            )
            min_salary = st.number_input("Minimum Salary ($)", value=pref.get("min_salary") or 0)
            remote_only = st.checkbox("Remote Only", value=pref.get("remote_only", False))
            submitted = st.form_submit_button("Save Preferences", use_container_width=True)

        if submitted:
            api_put("/api/settings/preferences", token, {
                "desired_titles": [t.strip() for t in titles_input.split("\n") if t.strip()],
                "desired_locations": [l.strip() for l in locations_input.split("\n") if l.strip()],
                "excluded_companies": [c.strip() for c in excluded_input.split("\n") if c.strip()],
                "min_salary": min_salary if min_salary > 0 else None,
                "remote_only": remote_only,
            })
            st.success("✅ Preferences saved!")


# ── Settings page ──

def settings_page(token: str) -> None:
    """Non-sensitive settings only."""
    st.title("🔧 Settings")
    st.info("⚠️ Sensitive credentials (SMTP, API keys) are managed via .env file only")

    config = api_get("/api/settings/config", token) or {}

    with st.form("settings_form"):
        scrape_interval = st.number_input(
            "Scrape Interval (minutes)",
            value=int(config.get("scrape_interval_minutes", 60)),
            min_value=5,
        )
        match_threshold = st.slider(
            "Match Threshold",
            0.0, 1.0,
            float(config.get("match_threshold", 0.65)),
            step=0.05,
        )
        max_apps = st.number_input(
            "Max Applications per Day",
            value=int(config.get("max_applications_per_day", 25)),
            min_value=1, max_value=100,
        )
        keywords = st.text_input(
            "Required Keywords (comma-separated)",
            config.get("required_keywords", ""),
        )
        submitted = st.form_submit_button("Save Settings", use_container_width=True)

    if submitted:
        api_put("/api/settings/config", token, {
            "scrape_interval_minutes": str(scrape_interval),
            "match_threshold": str(match_threshold),
            "max_applications_per_day": str(max_apps),
            "required_keywords": keywords,
        })
        st.success("✅ Settings saved!")


# ── Navigation ──

def main() -> None:
    """Main app entry point with sidebar navigation."""
    if not st.session_state.token:
        login_page()
        return

    token = st.session_state.token

    with st.sidebar:
        st.title("🎯 AutoApply AI")
        st.caption(f"Logged in as {st.session_state.user.get('email', '')}")
        st.divider()

        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "📄 Resumes", "💼 Jobs", "🎯 Matches",
             "📋 Applications", "⚙️ Preferences", "🔧 Settings"],
            label_visibility="collapsed",
        )

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()

    page_map = {
        "📊 Dashboard": dashboard_page,
        "📄 Resumes": resume_page,
        "💼 Jobs": jobs_page,
        "🎯 Matches": matches_page,
        "📋 Applications": applications_page,
        "⚙️ Preferences": preferences_page,
        "🔧 Settings": settings_page,
    }

    page_func = page_map.get(page, dashboard_page)
    page_func(token)


if __name__ == "__main__":
    main()
