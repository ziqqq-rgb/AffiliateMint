"""
Interactive entrypoint: discovers categories, asks on Telegram 5 at a
time, scrapes the chosen one - all inside a SINGLE app session, so
TikTok is only launched once per run instead of restarting between
steps.

Flow:
  1. You open the Product Ranking screen once, press Enter
  2. Bot shows top-level categories 5 at a time - pick one, or 'next'
  3. Bot scrolls to discover sections, showing them 5 at a time -
     picking one, 'next' for more, or 'back' to try a different
     top-level category instead. Scrolling only happens as far as
     needed for the page you're currently looking at, not the whole
     list upfront - see _pick_subcategory's docstring.
  4. Bot scrapes the resulting product list
"""

import difflib
import logging
import re

from scraper.filters import apply_filters
from scraper.mobile import navigate
from scraper.mobile.categories import discover_sub_categories, discover_top_tabs
from scraper.mobile.driver import app_session, human_delay
from scraper.mobile.ocr import extract_products, screenshot_to_lines, to_scraped_product_shape
from scraper.mobile.telegram_notify import (
    GO_BACK,
    NEXT_PAGE,
    wait_for_one_page,
    wait_for_paginated_choice,
)

logger = logging.getLogger(__name__)

PAGE_SIZE = 5

# How similar (0-1, via difflib) an OCR'd label needs to be to the
# originally-chosen text to count as "found it again" during re-scroll.
# OCR reads the same on-screen text slightly differently between two
# separate screenshots (extra/missing space, "&" vs "and", a dropped
# word) - comparing NORMALIZED text with a fuzzy threshold survives
# that jitter; exact string equality does not.
FUZZY_MATCH_THRESHOLD = 0.75


def scrape_interactive(max_scroll_attempts: int = 10) -> list[dict]:
    with app_session() as driver:
        human_delay()
        print("\nNavigate to the Product Ranking screen, then press Enter.")
        input()

        tabs = discover_top_tabs(driver.get_screenshot_as_png())
        if not tabs:
            raise RuntimeError("No category tabs found - is this really the Product Ranking screen?")
        tab_names = [t.text for t in tabs]

        chosen_subcat = None
        chosen_step = 0
        while chosen_subcat is None:
            logger.info("Sending %d top-level categories to Telegram.", len(tabs))
            chosen_tab = wait_for_paginated_choice(tab_names, allow_back=False)
            navigate.tap_label(driver, next(t for t in tabs if t.text == chosen_tab))
            human_delay()

            choice, step = _pick_subcategory(driver, max_scroll_attempts)
            if choice is GO_BACK:
                _scroll_to_top(driver, max_scroll_attempts)
                continue

            chosen_subcat, chosen_step = choice, step

        # Go back to exactly where we found it (fast path), then do a
        # short fuzzy-matched verification scroll to nail the tap -
        # don't blindly re-scan the whole list from zero every time.
        _scroll_to_top(driver, max_scroll_attempts)
        for _ in range(chosen_step):
            navigate.scroll_down(driver)
            human_delay()

        target = _find_by_scrolling(driver, chosen_subcat, verify_attempts=3)
        if target is None:
            # Fast path missed (scroll distance isn't perfectly
            # reproducible) - fall back to a full fuzzy re-scan before
            # giving up for real.
            _scroll_to_top(driver, max_scroll_attempts)
            target = _find_by_scrolling(driver, chosen_subcat, verify_attempts=max_scroll_attempts)

        if target is None:
            raise RuntimeError(
                f"Could not re-find {chosen_subcat!r} while scrolling back down. "
                "Try lowering FUZZY_MATCH_THRESHOLD in this file if the category "
                "name is being read noticeably differently between passes."
            )
        navigate.tap_label(driver, target)
        human_delay()

        # --- scrape the resulting product list screen ---
        png_bytes = driver.get_screenshot_as_png()

    lines = screenshot_to_lines(png_bytes)
    ocr_products = extract_products(lines, category=chosen_subcat)
    products = [to_scraped_product_shape(p) for p in ocr_products]

    # Mobile OCR never has stock_volume, and review_score isn't shown
    # on every screen - don't require either or every result gets
    # filtered out (see scraper/mobile/README.md known limitations).
    shortlist = apply_filters(products, require_stock=False, require_rating=False)
    if not shortlist:
        logger.warning(
            "Interactive scrape for %r returned 0 products passing filters (%d read off screen).",
            chosen_subcat,
            len(products),
        )
    return shortlist


def _pick_subcategory(driver, max_scroll_attempts: int):
    """Scrolls just enough to reveal one page (5) of sub-categories,
    sends that to Telegram immediately, and only scrolls FURTHER if you
    reply 'next' - this is the fix for the long silence before the
    first Telegram message: the old version scrolled through the
    WHOLE list (up to max_scroll_attempts screens) before sending
    anything at all, no matter how few items you actually wanted to see.

    Returns (chosen_text, step_found_at), or (GO_BACK, None).
    """
    found: dict = {}  # text -> (label, step)
    shown = 0
    step = 0
    consecutive_empty_scrolls = 0
    reached_bottom = False

    while True:
        while len(found) - shown < PAGE_SIZE and step < max_scroll_attempts:
            before = len(found)
            lines = screenshot_to_lines(driver.get_screenshot_as_png())
            for label in discover_sub_categories(lines):
                found.setdefault(label.text, (label, step))

            if len(found) == before:
                consecutive_empty_scrolls += 1
                if consecutive_empty_scrolls >= 2:
                    reached_bottom = True
                    break  # 2 scrolls with nothing new = we've hit the bottom, stop early
            else:
                consecutive_empty_scrolls = 0

            navigate.scroll_down(driver)
            human_delay()
            step += 1
        else:
            reached_bottom = step >= max_scroll_attempts

        names = list(found.keys())
        if not names:
            return GO_BACK, None  # nothing found at all under this category

        page = names[shown : shown + PAGE_SIZE]
        has_more = len(names) > shown + PAGE_SIZE or not reached_bottom
        logger.info("Sending sub-category page (%d found so far) to Telegram.", len(names))
        choice = wait_for_one_page(page, allow_next=has_more, allow_back=True)

        if choice is GO_BACK:
            return GO_BACK, None
        if choice is NEXT_PAGE:
            shown += len(page)
            continue
        return choice, found[choice][1]


def _find_by_scrolling(driver, target_text: str, verify_attempts: int):
    """Scrolls down up to `verify_attempts` times looking for the
    closest fuzzy match to target_text - tolerant of OCR reading the
    same on-screen text slightly differently between two passes."""
    target_key = _normalize(target_text)
    best_label, best_ratio = None, 0.0

    for _ in range(verify_attempts):
        lines = screenshot_to_lines(driver.get_screenshot_as_png())
        for label in discover_sub_categories(lines):
            ratio = difflib.SequenceMatcher(None, _normalize(label.text), target_key).ratio()
            if ratio > best_ratio:
                best_label, best_ratio = label, ratio
            if ratio == 1.0:  # exact normalized match - stop immediately, no need to keep scrolling
                return label
        navigate.scroll_down(driver)
        human_delay()

    return best_label if best_ratio >= FUZZY_MATCH_THRESHOLD else None


def _scroll_to_top(driver, max_scroll_attempts: int) -> None:
    for _ in range(max_scroll_attempts):
        navigate.scroll_up(driver)


def _normalize(text: str) -> str:
    """Strips whitespace/punctuation/case differences so 'Crisps &
    Puffed Snacks' and 'Crisps &Puffed Snacks' (OCR dropped one space)
    compare as equal."""
    return re.sub(r"[^a-z0-9]+", "", text.lower())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = scrape_interactive()
    print(f"Shortlisted {len(results)} products")
    for r in results:
        print(r)