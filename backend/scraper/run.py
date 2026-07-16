"""
Scraper entrypoint. FR-1.5: callable on a schedule (cron) or on demand
from the dashboard / MCP tool.

This is intentionally synchronous-looking from the outside (returns a
plain list of dicts) even though Playwright itself is async, so
callers (the FastMCP tool, a cron script, a test) don't need to know
that detail.
"""

import asyncio
import logging

from scraper.browser import human_delay, scraper_context
from scraper.config import config
from scraper.filters import apply_filters
from scraper.intercept import ResponseCollector, parse_response

logger = logging.getLogger(__name__)


def scrape_products(category: str, shortlist_size: int | None = None) -> list[dict]:
    """Synchronous wrapper around the async scrape - call this from the
    FastMCP tool, a CLI script, or a cron job."""
    return asyncio.run(_scrape_products_async(category))


async def _scrape_products_async(category: str) -> list[dict]:
    collector = ResponseCollector()

    async with scraper_context() as context:
        page = await context.new_page()
        collector.attach(page)

        search_url = config.search_url_template.format(query=category)
        await page.goto(search_url)
        await human_delay()

        # TODO: real scrolling/pagination logic goes here once you know
        # how TikTok Shop paginates search results.
        await page.wait_for_timeout(3000)

    products = []
    for raw in collector.raw_payloads:
        for item in parse_response(raw):
            item["est_commission_rm"] = round(
                item["price_rm"] * item["commission_percentage"] / 100, 2
            )
            products.append(item)

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
    results = scrape_products(category="mini fan")
    print(f"Shortlisted {len(results)} products")
