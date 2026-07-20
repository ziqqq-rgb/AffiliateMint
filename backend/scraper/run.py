"""
Scraper entrypoint. FR-1.5: callable on a schedule (cron) or on demand
from the dashboard / MCP tool.

Drives a real browser to the public storefront and lets TikTok's own
JS make the request; we just listen for the response
(scraper/intercept.py) instead of trying to fake the request
ourselves. This is intentionally synchronous-looking from the outside
(returns a plain list of dicts) even though Playwright itself is
async, so callers (the FastMCP tool, a cron script, a test) don't
need to know that detail.
"""

import asyncio
import json
import logging
from pathlib import Path

from scraper.browser import human_delay, scraper_context
from scraper.capture_session import CAPTURES_DIR
from scraper.config import config
from scraper.filters import apply_filters
from scraper.intercept import ResponseCollector, parse_response

logger = logging.getLogger(__name__)


def scrape_products_from_latest_capture() -> list[dict]:
    """Parses the most recent saved capture instead of driving a live
    browser. This is the day-to-day entrypoint: TikTok's anti-bot
    challenge blocks fully automated navigation (see
    scraper/capture_session.py), so capturing is a manual step you run
    yourself every so often; this function only does the deterministic
    parse + filter work on whatever was captured.
    """
    files = sorted(Path(CAPTURES_DIR).glob("capture_*.json"))
    if not files:
        raise FileNotFoundError(
            "No captures found - run `python -m scraper.capture_session` first."
        )

    raw_payloads = json.loads(files[-1].read_text())
    products = [item for raw in raw_payloads for item in parse_response(raw)]
    shortlist = apply_filters(products)

    if not shortlist:
        logger.warning(
            "Latest capture (%s) returned 0 products passing filters (%d raw items seen).",
            files[-1].name,
            len(products),
        )

    return shortlist


def scrape_products(category: str = "homepage") -> list[dict]:
    """Synchronous wrapper around the async, fully-automated scrape.

    NOTE: this will very likely get served TikTok's drag-puzzle
    challenge and return nothing - use
    `scrape_products_from_latest_capture()` for day-to-day use instead
    (see scraper/capture_session.py). Left here in case a
    well-warmed persistent profile ever gets through unattended; not
    the recommended path today.

    `category` is currently informational only - the only endpoint
    captured so far is the homepage feed, which isn't search/category
    scoped (see scraper/config.py).
    """
    return asyncio.run(_scrape_products_async(category))


async def _scrape_products_async(category: str) -> list[dict]:
    collector = ResponseCollector()

    async with scraper_context() as context:
        page = await context.new_page()
        collector.attach(page)

        await page.goto(config.search_url_template)
        await human_delay()

        # TODO: real scrolling/pagination logic goes here once the feed
        # is confirmed to load more products on scroll.
        await page.wait_for_timeout(3000)

    products = [item for raw in collector.raw_payloads for item in parse_response(raw)]
    shortlist = apply_filters(products)

    if not shortlist:
        # NFR 5.1 / FR-1.6: fail loudly, don't return an empty list silently.
        logger.warning(
            "Scrape run for %r returned 0 products passing filters (%d raw items seen).",
            category,
            len(products),
        )

    return shortlist


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = scrape_products()
    print(f"Shortlisted {len(results)} products")
    for r in results:
        print(r)
