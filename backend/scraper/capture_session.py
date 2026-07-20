"""
Human-in-the-loop capture session.

TikTok's public storefront actively fingerprints automation - a fully
automated, unattended Playwright script gets served a drag-puzzle
challenge ("Verify to continue") built to fail on bot-like input.
We're not building tooling that tries to defeat that check.

Instead: you drive the browser and solve the puzzle yourself (that's
the whole point of the check - proving a human's there). This
script's only job is to sit in the background and save every matching
API response it sees while you browse, so the deterministic part of
the pipeline (scraper/run.py's parse_response + apply_filters) can run
on real captured data afterward, with no automation anywhere near the
challenge.

Usage:
    cd backend
    python -m scraper.capture_session
    (browse shop.tiktok.com/my normally, solve the puzzle if it shows up,
     scroll around so more products load, visit a category if you want,
     then press Enter here to save what was captured)
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright

from scraper.browser import PROFILE_DIR
from scraper.config import config
from scraper.intercept import ResponseCollector

CAPTURES_DIR = Path("./scraper/.captures")


async def main() -> None:
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    collector = ResponseCollector()

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=False,  # always visible - a human needs to drive this
        )
        page = await context.new_page()
        collector.attach(page)
        await page.goto(config.search_url_template)

        print("\nBrowser is open. Browse shop.tiktok.com/my normally - solve the")
        print("puzzle if it appears, scroll to load more products, visit a category")
        print("or search if you want. Every matching API response gets captured.")
        input("Press Enter here once you're done browsing...\n")

        await context.close()

    if not collector.raw_payloads:
        print("No matching responses captured - nothing saved.")
        return

    out_path = CAPTURES_DIR / f"capture_{datetime.now():%Y%m%d_%H%M%S}.json"
    out_path.write_text(json.dumps(collector.raw_payloads))
    print(f"Saved {len(collector.raw_payloads)} raw response(s) to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
