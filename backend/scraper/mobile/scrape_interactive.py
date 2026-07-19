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

from scraper.mobile import driver
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



def scrape_interactive(max_scroll_attempts: int = 10) -> list[dict]:
    with app_session() as driver:
        human_delay()
        print("\nNavigate to the Product Ranking screen, then press Enter.")
        input()

        tabs = discover_top_tabs_vlm(driver.get_screenshot_as_png())
        if not tabs:
            raise RuntimeError("No category tabs found - is this really the Product Ranking screen?")
        tab_names = [t["text"] for t in tabs]

        chosen_label = None
        chosen_step = 0
        while chosen_label is None:
            logger.info("Sending %d top-level categories to Telegram.", len(tabs))
            chosen_tab_name = wait_for_paginated_choice(tab_names, allow_back=False)
            chosen_tab = next(t for t in tabs if t["text"] == chosen_tab_name)
            navigate.tap_xy(driver, chosen_tab["x"], chosen_tab["y"])
            human_delay()

            choice, step = _pick_subcategory(driver, max_scroll_attempts)
            if choice is GO_BACK:
                _scroll_to_top(driver, max_scroll_attempts)
                continue

            chosen_label, chosen_step = choice, step

        # Go back to exactly where we found it, then tap the EXACT
        # coordinates recorded at discovery time. We deliberately don't
        # re-search by heading text here: the heading isn't the tappable
        # thing, the "N new products" link next to it is - and we
        # already have its real coordinates, so searching again just
        # risks matching the wrong nearby element.
        _scroll_to_top(driver, max_scroll_attempts)
        for _ in range(chosen_step):
            navigate.scroll_down(driver)
            human_delay()

        navigate.tap_xy(driver, chosen_label["x"], chosen_label["y"])
        human_delay()

        if not _verify_landed_on(driver, chosen_label["text"]):
            raise RuntimeError(
                f"Tapped for {chosen_label['text']!r} but didn't land on that "
                f"page - the tap likely missed (scroll position drifted from "
                f"discovery time). Re-run and try again."
            )

        png_bytes = driver.get_screenshot_as_png()

    vlm_products = extract_products_vlm(png_bytes)
    products = [to_scraped_product_shape(p) for p in vlm_products]

    shortlist = apply_filters(products, require_stock=False, require_rating=False)
    if not shortlist:
        logger.warning(
            "Interactive scrape for %r returned 0 products passing filters (%d read off screen).",
            chosen_label["text"],
            len(products),
        )
    return shortlist


def _pick_subcategory(driver, max_scroll_attempts: int):
    """Returns (chosen_label, step_found_at), or (GO_BACK, None).
    chosen_label is the full {"text", "x", "y"} dict recorded at
    discovery time - .text is for display, .x/.y is the exact tap
    target (the "N new products" link, not the heading above it)."""
    found: dict = {}   # dedup_key -> (label_dict, step)
    order: list = []
    shown = 0
    step = 0
    consecutive_empty_scrolls = 0
    reached_bottom = False

    while True:
        while len(found) - shown < PAGE_SIZE and step < max_scroll_attempts:
            before = len(found)
            labels = discover_sub_categories_vlm(driver.get_screenshot_as_png())
            for label in labels:
                key = (label["text"], round(label["y"] / 50))
                if key not in found:
                    found[key] = (label, step)
                    order.append(key)

            if len(found) == before:
                consecutive_empty_scrolls += 1
                if consecutive_empty_scrolls >= 2:
                    reached_bottom = True
                    break
            else:
                consecutive_empty_scrolls = 0

            navigate.scroll_down(driver)
            human_delay()
            step += 1
        else:
            reached_bottom = step >= max_scroll_attempts

        if not order:
            return GO_BACK, None

        page_keys = order[shown : shown + PAGE_SIZE]
        page_names = [found[k][0]["text"] for k in page_keys]
        has_more = len(order) > shown + PAGE_SIZE or not reached_bottom
        logger.info("Sending sub-category page (%d found so far) to Telegram.", len(order))
        choice_name = wait_for_one_page(page_names, allow_next=has_more, allow_back=True)

        if choice_name is GO_BACK:
            return GO_BACK, None
        if choice_name is NEXT_PAGE:
            shown += len(page_keys)
            continue

        chosen_key = page_keys[page_names.index(choice_name)]
        chosen_label, chosen_step = found[chosen_key]
        return chosen_label, chosen_step



def _scroll_to_top(driver, max_scroll_attempts: int) -> None:
    for _ in range(max_scroll_attempts):
        navigate.scroll_up(driver)

def _verify_landed_on(driver, expected_title: str) -> bool:
    """After tapping a sub-category, confirm we actually landed on its
    page (checks for the big title text at the top of screen, e.g.
    'Candy') instead of blindly trusting the tap worked. Real-device
    swipes don't always move the same distance twice, so the tap
    coordinates we recorded during discovery can miss - this catches
    that instead of silently scraping the wrong screen."""
    png_bytes = driver.get_screenshot_as_png()
    match = find_label_vlm(png_bytes, expected_title)
    return match is not None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = scrape_interactive()
    print(f"Shortlisted {len(results)} products")
    for r in results:
        print(r)