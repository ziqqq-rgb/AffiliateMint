"""
Interactive entrypoint: discovers categories, asks on Telegram 5 at a
time, scrapes the chosen one - all inside a SINGLE app session, so
TikTok is only launched once per run instead of restarting between
steps.

Every screen-reading and tap-target decision here comes from the VLM
agent (vlm_agent.py) - no OCR, no regex, no fuzzy string matching.
That's the deliberate fix for the class of bugs the OCR version hit
repeatedly: a category not being "found" because a regex expected
exact wording TikTok phrased slightly differently. The VLM is asked
the same question a human would answer by looking at the screen:
"is this label here, and if so, where do I tap?"

Flow (unchanged from the OCR version):
  1. You open the Product Ranking screen once, press Enter
  2. Bot shows top-level categories 5 at a time - pick one, or 'next'
  3. Bot scrolls to discover sections, showing them 5 at a time -
     picking one, 'next' for more, or 'back' to try a different
     top-level category instead.
  4. Bot scrapes the resulting product list
"""

import logging

from scraper.filters import apply_filters
from scraper.mobile import navigate
from scraper.mobile.driver import app_session, human_delay
from scraper.mobile.telegram_notify import (
    GO_BACK,
    NEXT_PAGE,
    wait_for_one_page,
    wait_for_paginated_choice,
)
from scraper.mobile.vlm_agent import discover_sub_categories_vlm, discover_top_tabs_vlm, find_label_vlm
from scraper.mobile.vlm_extract import extract_products_vlm, to_scraped_product_shape

logger = logging.getLogger(__name__)

PAGE_SIZE = 5


def _ask_operator_to_repick(driver, original_choice: str):
    """VLM couldn't re-find `original_choice` after two passes. Rather
    than crashing the whole run, show whatever IS visible right now and
    let a human pick - cheaper than losing the entire scrape."""
    visible = discover_sub_categories_vlm(driver.get_screenshot_as_png())
    if not visible:
        raise RuntimeError(f"Nothing visible on screen to re-pick {original_choice!r} from.")

    logger.warning("Could not re-find %r automatically - asking operator.", original_choice)
    names = [label["text"] for label in visible]
    choice = wait_for_one_page(names, allow_next=False, allow_back=False)
    return next(label for label in visible if label["text"] == choice)


def scrape_interactive(max_scroll_attempts: int = 10) -> list[dict]:
    with app_session() as driver:
        human_delay()
        print("\nNavigate to the Product Ranking screen, then press Enter.")
        input()

        tabs = discover_top_tabs_vlm(driver.get_screenshot_as_png())
        if not tabs:
            raise RuntimeError("No category tabs found - is this really the Product Ranking screen?")
        tab_names = [t["text"] for t in tabs]

        chosen_subcat = None
        chosen_step = 0
        while chosen_subcat is None:
            logger.info("Sending %d top-level categories to Telegram.", len(tabs))
            chosen_tab_name = wait_for_paginated_choice(tab_names, allow_back=False)
            chosen_tab = next(t for t in tabs if t["text"] == chosen_tab_name)
            navigate.tap_xy(driver, chosen_tab["x"], chosen_tab["y"])
            human_delay()

            choice, step = _pick_subcategory(driver, max_scroll_attempts)
            if choice is GO_BACK:
                _scroll_to_top(driver, max_scroll_attempts)
                continue

            chosen_subcat, chosen_step = choice, step

        # Go back to exactly where we found it (fast path), then do a
        # short verification scroll to confirm the tap target still
        # matches - don't blindly re-scan the whole list from zero.
        _scroll_to_top(driver, max_scroll_attempts)
        for _ in range(chosen_step):
            navigate.scroll_down(driver)
            human_delay()

        target = _find_by_scrolling(driver, chosen_subcat, verify_attempts=3)
        if target is None:
            _scroll_to_top(driver, max_scroll_attempts)
            target = _find_by_scrolling(driver, chosen_subcat, verify_attempts=max_scroll_attempts)

        if target is None:
            target = _ask_operator_to_repick(driver, chosen_subcat)  # last resort: human picks, doesn't crash

        navigate.tap_xy(driver, target["x"], target["y"])
        human_delay()

        # --- scrape the resulting product list screen ---
        png_bytes = driver.get_screenshot_as_png()

    vlm_products = extract_products_vlm(png_bytes)
    products = [to_scraped_product_shape(p) for p in vlm_products]

    # Mobile scrapes never have stock_volume, and review_score isn't
    # shown on every screen - don't require either or every result
    # gets filtered out (see scraper/mobile/README.md known limitations).
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
    reply 'next' - avoids scrolling through the whole list before
    sending anything.

    Returns (chosen_text, step_found_at), or (GO_BACK, None).
    """
    found: dict = {}  # text -> (label_dict, step)
    shown = 0
    step = 0
    consecutive_empty_scrolls = 0
    reached_bottom = False

    while True:
        while len(found) - shown < PAGE_SIZE and step < max_scroll_attempts:
            before = len(found)
            labels = discover_sub_categories_vlm(driver.get_screenshot_as_png())
            for label in labels:
                found.setdefault(label["text"], (label, step))

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


def _find_by_scrolling(driver, target_text: str, verify_attempts: int) -> dict | None:
    """Scrolls down up to `verify_attempts` times asking the VLM if
    `target_text` is on screen yet. The model handles minor wording
    drift itself (see find_label_vlm's prompt), so no fuzzy-matching
    code is needed here."""
    for _ in range(verify_attempts):
        found = find_label_vlm(driver.get_screenshot_as_png(), target_text)
        if found is not None:
            return found
        navigate.scroll_down(driver)
        human_delay()
    return None


def _scroll_to_top(driver, max_scroll_attempts: int) -> None:
    for _ in range(max_scroll_attempts):
        navigate.scroll_up(driver)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = scrape_interactive()
    print(f"Shortlisted {len(results)} products")
    for r in results:
        print(r)