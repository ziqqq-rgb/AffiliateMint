"""
Manual browsing helper for finding TikTok Shop's real endpoints.

The public storefront doesn't require login, but this still opens a
REAL, visible browser window using the same persistent profile the
scraper uses (scraper/browser.py's PROFILE_DIR) - useful whenever you
need to manually browse to a page (a category, a search result) and
capture ITS network endpoint the same way the homepage feed was
captured, since only the homepage is wired up in scraper/config.py today.

Usage:
    cd backend
    python -m scraper.login_helper
"""

import asyncio

from playwright.async_api import async_playwright

from scraper.browser import PROFILE_DIR
from scraper.config import config

START_URL = config.search_url_template


async def main() -> None:
    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=False,  # always visible - the whole point is manual browsing
        )
        page = await context.new_page()
        await page.goto(START_URL)

        print("\nBrowser is open. Browse to the page you want to capture (a category,")
        print("a search result, etc.) and open DevTools -> Network -> XHR to find its")
        print("product-list endpoint, the same way the homepage feed was found.")
        input("Press Enter here once you're done (this keeps the session/profile saved)...\n")

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
