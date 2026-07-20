"""
Playwright browser session management.

Uses a dedicated, persistent browser profile so the scraper looks
like a normal returning visitor across runs instead of a fresh
anonymous session every time - and centralizes the one place that
launches/closes the browser so every other scraper module just gets a
ready-to-use page.
"""

import asyncio
import random
from contextlib import asynccontextmanager

from playwright.async_api import BrowserContext, async_playwright

from app.config import settings
from scraper.config import config

PROFILE_DIR = "./scraper/.browser_profile"


@asynccontextmanager
async def scraper_context():
    """Yields a ready Playwright BrowserContext using a persistent, dedicated profile."""
    async with async_playwright() as playwright:
        context: BrowserContext = await playwright.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=settings.scraper_headless,
        )
        try:
            yield context
        finally:
            await context.close()


async def human_delay() -> None:
    """NFR 5.2: randomized delay between actions, not machine-regular timing."""
    delay = random.uniform(config.min_delay_seconds, config.max_delay_seconds)
    await asyncio.sleep(delay)
