"""
One-time (or occasional) manual login helper.

Run this whenever your saved TikTok Shop session has expired, or the
very first time you set up the scraper. It opens a REAL, visible
browser window using the same persistent profile the scraper uses
(scraper/browser.py's PROFILE_DIR), so once you log in here, every
future scraper run - headless or not - stays logged in as you.

This is also the easiest way to find TikTok's real product-search
endpoint for scraper/config.py + scraper/intercept.py: once you're
logged in, open DevTools -> Network -> XHR, search a product, and
look for the response that contains price/commission/stock data.

Usage:
    cd backend
    python -m scraper.login_helper
"""

import asyncio

from playwright.async_api import async_playwright

from scraper.browser import PROFILE_DIR

# TODO: point this at wherever you actually browse products with
# commission data - for most MY affiliates that's the Affiliate
# Center's "Find products" page, not the plain shop.tiktok.com
# storefront (which doesn't show commission %).
START_URL = "https://affiliate.tiktok.com/"


async def main() -> None:
    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=False,  # always visible - the whole point is manual login
        )
        page = await context.new_page()
        await page.goto(START_URL)

        print("\nBrowser is open. Log in manually, then browse to a product")
        print("search and open DevTools -> Network -> XHR to inspect responses.")
        input("Press Enter here once you're done (this keeps the session saved)...\n")

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
