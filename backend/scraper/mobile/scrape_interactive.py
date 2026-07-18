"""
Interactive entrypoint: discovers categories, asks once on Telegram,
scrapes the chosen one - all inside a SINGLE app session, so TikTok
is only launched once per run instead of restarting between steps.
"""

import logging

from scraper.mobile import navigate
from scraper.mobile.categories import discover_sub_categories, discover_top_tabs
from scraper.mobile.driver import app_session, human_delay
from scraper.mobile.ocr import extract_products, screenshot_to_lines, to_scraped_product_shape
from scraper.mobile.telegram_notify import send_category_choices, wait_for_category_choice

logger = logging.getLogger(__name__)


def scrape_interactive(max_scroll_attempts: int = 10) -> list[dict]:
    """You still open the Product Ranking screen yourself once at the
    start - there's no reliable text-based way to find TikTok's
    home-screen nav icons on a screen that's ALSO all images/canvas.
    Everything after that is autonomous: tab choice, section choice,
    and the final scrape all happen through Telegram + OCR, no more
    manual taps needed.
    """
    with app_session() as driver:
        human_delay()
        print("\nNavigate to the Product Ranking screen, then press Enter.")
        input()

        # --- Step 1: pick a top-level category tab ---
        tabs = discover_top_tabs(driver.get_screenshot_as_png())
        if not tabs:
            raise RuntimeError("No category tabs found - is this really the Product Ranking screen?")

        tab_names = [t.text for t in tabs]
        logger.info("Found %d top-level categories - sending to Telegram.", len(tabs))
        send_category_choices(tab_names)
        chosen_tab = wait_for_category_choice(tab_names)
        navigate.tap_label(driver, next(t for t in tabs if t.text == chosen_tab))
        human_delay()

        # --- Step 2: pick a specific section within that category ---
        subcats = _discover_subcategories_by_scrolling(driver, max_scroll_attempts)
        if not subcats:
            raise RuntimeError("No sub-category sections found after scrolling.")

        subcat_names = list(subcats.keys())
        logger.info("Found %d sub-categories - sending to Telegram.", len(subcat_names))
        send_category_choices(subcat_names)
        chosen_subcat = wait_for_category_choice(subcat_names)

        # Scroll back to the top, then re-scroll down re-reading the
        # screen until the chosen one is visible again - simpler and
        # more robust than trying to remember an exact scroll offset.
        for _ in range(max_scroll_attempts):
            navigate.scroll_up(driver)

        target = _find_by_scrolling(driver, chosen_subcat, max_scroll_attempts)
        if target is None:
            raise RuntimeError(f"Could not re-find {chosen_subcat!r} while scrolling back down.")
        navigate.tap_label(driver, target)
        human_delay()

        # --- Step 3: scrape the resulting product list screen ---
        png_bytes = driver.get_screenshot_as_png()

    lines = screenshot_to_lines(png_bytes)
    ocr_products = extract_products(lines, category=chosen_subcat)
    products = [to_scraped_product_shape(p) for p in ocr_products]

    from scraper.filters import apply_filters  # local import - keeps this module's import-time deps minimal

    shortlist = apply_filters(products)
    if not shortlist:
        logger.warning(
            "Interactive scrape for %r returned 0 products passing filters (%d read off screen).",
            chosen_subcat,
            len(products),
        )
    return shortlist


def _discover_subcategories_by_scrolling(driver, max_scroll_attempts: int) -> dict:
    found: dict = {}
    for _ in range(max_scroll_attempts):
        lines = screenshot_to_lines(driver.get_screenshot_as_png())
        for label in discover_sub_categories(lines):
            found.setdefault(label.text, label)
        navigate.scroll_down(driver)
        human_delay()
    return found


def _find_by_scrolling(driver, target_text: str, max_scroll_attempts: int):
    for _ in range(max_scroll_attempts):
        lines = screenshot_to_lines(driver.get_screenshot_as_png())
        for label in discover_sub_categories(lines):
            if label.text == target_text:
                return label
        navigate.scroll_down(driver)
        human_delay()
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = scrape_interactive()
    print(f"Shortlisted {len(results)} products")
    for r in results:
        print(r)
