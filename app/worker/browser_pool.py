"""
Playwright browser pool with semaphore-controlled concurrency.

Reuses a single browser instance; caps concurrent pages.
"""

from __future__ import annotations

import asyncio
import threading
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from playwright.async_api import Browser, Page, Playwright


class BrowserPool:
    """
    Manages a pool of Playwright browser pages with concurrency limits.

    Uses a single Chromium browser instance and an asyncio.Semaphore
    to cap the number of concurrent pages.
    """

    _instance: BrowserPool | None = None
    _lock = threading.Lock()

    def __init__(self, max_size: int = 3) -> None:
        self._max_size = max_size
        self._semaphore: asyncio.Semaphore | None = None
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._initialized = False

    @classmethod
    def get_instance(cls, max_size: int = 3) -> BrowserPool:
        """Return singleton BrowserPool instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(max_size=max_size)
        return cls._instance

    async def _ensure_initialized(self) -> None:
        """Lazily initialize Playwright and browser on first use."""
        if self._initialized:
            return

        from playwright.async_api import async_playwright

        logger.info("Initializing Playwright browser pool (max_size={})", self._max_size)
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        self._semaphore = asyncio.Semaphore(self._max_size)
        self._initialized = True
        logger.info("Browser pool initialized")

    @asynccontextmanager
    async def acquire_page(self) -> AsyncIterator[Page]:
        """
        Acquire a browser page from the pool.

        Blocks if all slots are in use (semaphore limit).
        Automatically closes the page on exit.
        """
        await self._ensure_initialized()
        assert self._semaphore is not None
        assert self._browser is not None

        async with self._semaphore:
            page = await self._browser.new_page()
            try:
                # Apply stealth if available
                try:
                    from playwright_stealth import stealth_async
                    await stealth_async(page)
                except ImportError:
                    pass  # stealth not installed, proceed without

                yield page
            finally:
                try:
                    await page.close()
                except Exception:
                    pass  # Page may already be closed

    async def shutdown(self) -> None:
        """Close browser and Playwright."""
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

        self._initialized = False
        logger.info("Browser pool shut down")
