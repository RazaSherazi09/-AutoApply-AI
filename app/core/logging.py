"""
Structured, rotating file logging via Loguru.
Call ``setup_logging()`` once at application startup.
"""

from __future__ import annotations

import sys

from loguru import logger

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure loguru sinks: stderr (dev) + rotating JSON file (prod)."""
    settings = get_settings()

    # Remove default handler
    logger.remove()

    # Stderr sink — human-readable for development
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # Rotating file sink — structured JSON for production analysis
    logger.add(
        settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DDTHH:mm:ss.SSSZ} | {level} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        serialize=True,  # JSON output
        enqueue=True,  # thread-safe
    )

    logger.info("Logging initialized (level={})", settings.log_level)
