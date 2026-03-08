"""
FastAPI application entrypoint with lifespan, CORS, and router mounts.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup / shutdown lifecycle."""
    # ── Startup ──
    setup_logging()

    from loguru import logger
    logger.info("Starting AutoApply AI...")

    # Create DB tables (dev convenience; use Alembic in production)
    await init_db()
    logger.info("Database initialized")

    # Start background scheduler
    from app.worker.scheduler import start_scheduler, stop_scheduler
    start_scheduler()
    logger.info("Scheduler started")

    # Create upload directory
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    yield

    # ── Shutdown ──
    stop_scheduler()

    # Shut down browser pool if initialized
    try:
        from app.worker.browser_pool import BrowserPool
        pool = BrowserPool._instance
        if pool is not None:
            await pool.shutdown()
    except Exception:
        pass  # Playwright may not be installed

    logger.info("AutoApply AI shut down")


app = FastAPI(
    title="AutoApply AI",
    description="Local-first intelligent job application automation agent",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Mount routers
from app.api.routes.auth import router as auth_router
from app.api.routes.resumes import router as resumes_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.matches import router as matches_router
from app.api.routes.applications import router as applications_router
from app.api.routes.settings import router as settings_router

app.include_router(auth_router)
app.include_router(resumes_router)
app.include_router(jobs_router)
app.include_router(matches_router)
app.include_router(applications_router)
app.include_router(settings_router)


@app.get("/health")
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok", "service": "autoapply-ai"}
