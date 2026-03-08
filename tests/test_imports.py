"""
Step 1: Import Validation — Test every module imports cleanly.
"""
import sys, importlib, traceback

modules = [
    "app",
    "app.core",
    "app.core.config",
    "app.core.logging",
    "app.core.security",
    "app.core.database",
    "app.models",
    "app.models.base",
    "app.models.user",
    "app.models.resume",
    "app.models.job",
    "app.models.match",
    "app.models.application",
    "app.models.preference",
    "app.models.notification",
    "app.models.setting",
    "app.models.scraper_run",
    "app.schemas",
    "app.schemas.auth",
    "app.schemas.resume",
    "app.schemas.job",
    "app.schemas.match",
    "app.schemas.application",
    "app.schemas.preference",
    "app.services",
    "app.services.embedding",
    "app.services.resume_parser",
    "app.services.job_skill_extractor",
    "app.services.matcher",
    "app.services.notification",
    "app.services.auto_apply",
    "app.services.form_filler",
    "app.services.scraper_service",
    "app.scrapers",
    "app.scrapers.base",
    "app.scrapers.adzuna",
    "app.scrapers.career_page",
    "app.scrapers.greenhouse_api",
    "app.scrapers.lever_api",
    "app.scrapers.workday_api",
    "app.worker.browser_pool",
    "app.worker.scheduler",
    "app.api",
    "app.api.deps",
    "app.api.routes",
    "app.api.routes.auth",
    "app.api.routes.resumes",
    "app.api.routes.jobs",
    "app.api.routes.matches",
    "app.api.routes.applications",
    "app.api.routes.settings",
    "app.main",
]

passed = 0
failed = 0
errors = []

for mod in modules:
    try:
        importlib.import_module(mod)
        print(f"  OK  {mod}")
        passed += 1
    except Exception as e:
        print(f"  FAIL {mod}: {e}")
        errors.append((mod, str(e), traceback.format_exc()))
        failed += 1

print(f"\n{'='*60}")
print(f"RESULT: {passed} passed, {failed} failed out of {len(modules)}")
if errors:
    print(f"\nFAILURES:")
    for mod, err, tb in errors:
        print(f"\n--- {mod} ---")
        print(tb[-500:])
