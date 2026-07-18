# backend/scraper/mobile/scrape.py
"""
Mobile scraper entrypoint - the AI-vision equivalent of scraper/run.py.

TikTok's product-browsing screens render everything as images/canvas
(confirmed empirically - see mobile/README.md), so there is no
accessibility tree to read. Screenshots are sent to a vision model
(scraper/mobile/ai_extract.py) instead of OCR - this replaced the
original OCR+regex approach after repeated misreads on price fields
(see debug_ocr.py / debug_ai_extract.py for the comparison).

Returns the same shape as scraper/run.py so
app/mcp_tools/scraper_tool.py can call either implementation.
"""

import logging

from scraper.filters import apply_filters
from scraper.mobile import navigate
from scraper.mobile.ai_extract import extract_products_with_ai
from scraper.mobile.driver import app_session, human_delay

logger = logging.getLogger(__name__)


def scrape_products(product_type: str, max_scrolls: int = 6) -> list[dict]:
    """Launches TikTok, navigates to the Product ranking screen, drills
    into the full list for `product_type`, then scrolls + reads each
    screen with AI vision until no new products appear."""
    with app_session() as driver:
        human_delay()
        navigate.navigate_to_product_ranking(driver)
        navigate.open_product_type_list(driver, product_type)
        ai_products = _collect_by_scrolling(driver, max_scrolls)

    products = [_to_scraped_product_shape(p) for p in ai_products]
    shortlist = apply_filters(products)

    if not shortlist:
        # NFR 5.1 / FR-1.6: fail loudly, same rule as the other scrapers.
        logger.warning(
            "Mobile scrape for %r returned 0 products passing filters "
            "(%d read off screen).",
            product_type,
            len(products),
        )
    return shortlist


def _collect_by_scrolling(driver, max_scrolls: int) -> list[dict]:
    """One screen only shows ~4 products, so screenshot -> scroll ->
    repeat. Stops early once a scroll brings up nothing new (bottom
    of the list reached)."""
    seen_titles: set[str] = set()
    collected: list[dict] = []

    for _ in range(max_scrolls):
        png_bytes = driver.get_screenshot_as_png()
        page_products = extract_products_with_ai(png_bytes)

        new_products = [p for p in page_products if p["title"] not in seen_titles]
        if not new_products:
            break

        collected.extend(new_products)
        seen_titles.update(p["title"] for p in new_products)

        navigate.scroll_down(driver)
        human_delay()

    return collected


def _to_scraped_product_shape(p: dict) -> dict:
    """Converts the AI's output into the same dict shape
    scraper/filters.py and app/models.py expect."""
    price = p["price_rm"]
    commission_rm = p["commission_rm"]
    return {
        "title": p["title"],
        "price_rm": price,
        "commission_percentage": round((commission_rm / price) * 100, 2) if price else 0.0,
        "est_commission_rm": commission_rm,
        "review_score": p["review_score"],
        "stock_volume": 0,  # not shown on any screen we've found so far - same as OCR path
        "units_sold": p["units_sold"],
        "product_url": "",  # no URL available from a screenshot
        "raw_payload": p["title"],  # FR-1.4 spirit: keep something traceable per product
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = scrape_products(product_type="Chocolate & Chocolate Snacks")
    print(f"Shortlisted {len(results)} products")
    for r in results:
        print(r)