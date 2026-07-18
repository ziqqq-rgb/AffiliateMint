"""
Mobile scraper entrypoint - the OCR-based equivalent of scraper/run.py.

TikTok's product-browsing screens render everything as images/canvas
(confirmed empirically - see mobile/README.md), so there is no
accessibility tree to read. locators.py's original element-ID plan
cannot work here, no matter how it's tuned - this reads the screen
with OCR instead (scraper/mobile/ocr.py).

Returns the same shape as scraper/run.py so
app/mcp_tools/scraper_tool.py can call either implementation.
"""

import logging

from scraper.filters import apply_filters
from scraper.mobile.driver import app_session, human_delay
from scraper.mobile.ocr import extract_products, screenshot_to_lines

logger = logging.getLogger(__name__)


def scrape_products(category: str = "current screen") -> list[dict]:
    """Launches TikTok, waits for you to navigate to the right screen, then
    OCRs whatever's on screen.

    Every new Appium session force-launches the app to its home/splash
    screen - it can NOT resume wherever you last had it open, even
    though `no_reset=True` keeps you logged in. So this pauses and
    waits for you to manually navigate before taking the screenshot.
    `category` is only used for the log message, not navigation.
    """
    with app_session() as driver:
        human_delay()
        print("\nTikTok just relaunched to its home screen (this always happens when")
        print("a new automation session starts - it can't resume wherever you were).")
        print("Navigate to the product screen you want scraped (e.g. Product ranking).")
        input("Press Enter here once that screen is on screen and ready...\n")

        png_bytes = driver.get_screenshot_as_png()

    lines = screenshot_to_lines(png_bytes)
    ocr_products = extract_products(lines)

    products = [_to_scraped_product_shape(p) for p in ocr_products]
    shortlist = apply_filters(products)

    if not shortlist:
        # NFR 5.1 / FR-1.6: fail loudly, same rule as the other scrapers.
        # Extra context here because OCR screens often don't show every
        # field the web scraper expects (see the note below).
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
        "raw_payload": p["raw_ocr_text"],  # FR-1.4 spirit: keep the raw read, even though it's OCR text not JSON
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = scrape_products(category="product ranking screen")
    print(f"Shortlisted {len(results)} products")
    for r in results:
        print(r)
