"""
Mobile scraper entrypoint - the OCR-based equivalent of scraper/run.py.

TikTok's product-browsing screens render everything as images/canvas
(confirmed empirically - see mobile/README.md), so there is no
accessibility tree to read. This reads the screen with OCR instead
(scraper/mobile/ocr.py), after navigate.py taps its way there
automatically (scraper/mobile/navigate.py).

Returns the same shape as scraper/run.py so
app/mcp_tools/scraper_tool.py can call either implementation.
"""

import logging

from scraper.filters import apply_filters
from scraper.mobile import navigate
from scraper.mobile.driver import app_session, human_delay
from scraper.mobile.ocr import extract_products, screenshot_to_lines

logger = logging.getLogger(__name__)


def scrape_products(product_type: str) -> list[dict]:
    """Launches TikTok, navigates to the Product ranking screen, drills
    into the full list for `product_type` (e.g. "Tea"), then OCRs the
    result list - this is the screen with both price and commission
    (the ranking overview alone doesn't have enough data to compute
    commission_percentage).

    Raises navigate.NavigationError if a tap doesn't land where
    expected - see navigate.py's module docstring for why that's a
    hard failure rather than a silent continue (NFR 5.1).
    """
    with app_session() as driver:
        human_delay()
        navigate.navigate_to_product_ranking(driver)
        navigate.open_product_type_list(driver, product_type)

        png_bytes = driver.get_screenshot_as_png()

    lines = screenshot_to_lines(png_bytes)
    ocr_products = extract_products(lines)

    products = [_to_scraped_product_shape(p) for p in ocr_products]
    shortlist = apply_filters(products)

    if not shortlist:
        # NFR 5.1 / FR-1.6: fail loudly, same rule as the other scrapers.
        logger.warning(
            "OCR scrape for %r returned 0 products passing filters (%d read "
            "off screen). Note: stock_volume is never available via OCR on "
            "these screens (defaults to 0), and review_score is 0 on screens "
            "that don't display a rating - if either filter threshold in "
            "scraper/config.py is above 0, OCR results may always get "
            "filtered out. Consider a separate, more lenient threshold set "
            "for the mobile path.",
            category,
            len(products),
        )
    return shortlist


def _to_scraped_product_shape(p: dict) -> dict:
    """Converts an OCR'd card (flat 'Earn RMx.xx' commission) into the
    same dict shape scraper/filters.py and app/models.py expect
    (commission as a %, plus an explicit est_commission_rm)."""
    price = p["price_rm"]
    commission_rm = p["commission_rm"]
    return {
        "title": p["title"],
        "price_rm": price,
        "commission_percentage": round((commission_rm / price) * 100, 2) if price else 0.0,
        "est_commission_rm": commission_rm,
        "review_score": p["review_score"],
        "stock_volume": 0,  # not shown on any OCR'd screen we've found so far
        "units_sold": p["units_sold"],
        "product_url": "",  # OCR has no URL to offer
        "raw_payload": p["raw_ocr_text"],  # FR-1.4 spirit: never lose the raw read
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = scrape_products(product_type="Tea")
    print(f"Shortlisted {len(results)} products")
    for r in results:
        print(r)