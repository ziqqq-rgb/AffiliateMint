"""
backend/scraper/navigation.py

On-site UI navigation: category selection and filter/sort chips on TikTok
Shop's storefront. Runs BEFORE scraper/run.py starts harvesting.

Kept separate from run.py (the harvest loop) and intercept.py (JSON
parsing) on purpose: this file only clicks things, it never reads
product data. Uses Playwright's locator API (auto-waiting) instead of
manual time.sleep() - locators retry until visible/clickable or the
timeout fires.

Selectors are text/role based since TikTok Shop ships no stable
data-testid hooks on this UI. If TikTok renames a label, this is the
only file that needs an update - same principle as scraper/config.py's
target_endpoint_pattern. NOT yet confirmed against a live DevTools
session - verify CATEGORY_FILTERS the same way the endpoint pattern
was captured before relying on them.

IMPORTANT: category clicks can open a NEW TAB. Every function that might
navigate returns the currently-active Page - callers must use that
returned page for anything after, not their original reference, or
they'll hit TargetClosedError on a page TikTok/SeleniumBase already
closed.
"""
from __future__ import annotations

import logging
import random
import re
import time

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from scraper.config import config

logger = logging.getLogger(__name__)

# Regex patterns for filter/sort chip labels - one place to fix if TikTok
# changes its UI copy. Values are matched case-insensitively against the
# visible button text.
CATEGORY_FILTERS = {
    "sold_sort": "Best sellers|Most sold|Sales",
    "price_chip": "Price",
    "price_apply": "Apply|Confirm|OK",
}


def get_active_page(browser, url_hint: str = "tiktok", timeout_ms: int = 10000) -> Page:
    """CDP connections don't guarantee contexts[0].pages[0] is the tab you
    navigated - some SeleniumBase/incognito setups expose extra contexts
    with zero pages, or the tab takes a moment to register. Searches every
    context/page for one already on the target site, retrying briefly.
    Falls back to the first page found anywhere if nothing matches.
    """
    deadline = time.time() + (timeout_ms / 1000)
    fallback = None
    while time.time() < deadline:
        for context in browser.contexts:
            for page in context.pages:
                if fallback is None:
                    fallback = page
                if url_hint in page.url.lower():
                    return page
        time.sleep(0.3)
    if fallback:
        return fallback
    raise RuntimeError("No open page found in any browser context.")


def _human_pause() -> None:
    """Randomized delay between UI actions - same anti-bot spacing
    scraper/browser.py's scroll_infinite already uses (NFR 5.2). A
    click->click->click burst with zero delay is a stronger bot
    signal than scrolling, and TikTok's risk control responds to it
    with API error codes (e.g. code 100000) instead of data."""
    time.sleep(random.uniform(config.min_delay_seconds, config.max_delay_seconds))


def _safe_wait(page: Page, ms: int = 5000) -> None:
    """wait_for_timeout raises TargetClosedError if the page died mid-wait
    (e.g. a category click opened a new tab and the old one got closed).
    Checks is_closed() first so we skip the call entirely - a closed page
    isn't fatal to the scrape, this logs and moves on."""
    if page.is_closed():
        logger.warning("[!] Skipped wait - page already closed")
        return
    try:
        page.wait_for_timeout(ms)
    except PlaywrightTimeoutError:
        pass
    except Exception as e:
        if "closed" in str(e).lower():
            logger.warning(f"[!] Page closed during wait, continuing: {e}")
        else:
            raise


def nearest_rating_tier(min_rating: float, tiers: tuple[float, ...]) -> float:
    """Pure helper: TikTok Shop only offers a few fixed rating buckets (e.g.
    4.0+, 4.5+), not an arbitrary slider. Picks the smallest tier that still
    satisfies min_rating, falling back to the highest tier if none do.
    No Playwright dependency - unit testable on its own.
    """
    eligible = [t for t in tiers if t >= min_rating]
    return min(eligible) if eligible else max(tiers)


def open_category(page: Page, category_name: str, timeout_ms: int = 8000) -> Page:
    """Clicks a category tile in the homepage's "Categories" row. Returns
    the active Page afterward - TikTok Shop sometimes opens category tiles
    in a new tab, which would otherwise silently orphan the caller's
    original `page` reference.

    Returns the original page unchanged if the tile was never found or no
    new tab opened - this function never raises.
    """
    tile = page.get_by_text(category_name, exact=False).first
    try:
        tile.wait_for(state="visible", timeout=timeout_ms)
        tile.scroll_into_view_if_needed()

        context = page.context
        pages_before = set(context.pages)

        tile.click()
        _safe_wait(page, 1500)  # give a possible new tab time to open

        new_pages = [p for p in context.pages if p not in pages_before]
        active_page = new_pages[-1] if new_pages else page

        active_page.wait_for_load_state("domcontentloaded")
        logger.info(f"[+] Opened category: {category_name}")
        return active_page
    except PlaywrightTimeoutError:
        logger.warning(f"[!] Category tile not found: {category_name}")
        return page


def _click_chip(page: Page, label_pattern: str, timeout_ms: int = 5000) -> bool:
    """Shared helper: finds a filter/sort chip by visible text and clicks
    it. Every apply_* function below goes through this, so there's one
    place to fix if TikTok changes how chips render."""
    chip = page.get_by_role("button", name=re.compile(label_pattern, re.I)).first
    try:
        chip.wait_for(state="visible", timeout=timeout_ms)
        chip.click()
        return True
    except PlaywrightTimeoutError:
        logger.warning(f"[!] Filter chip not found: {label_pattern}")
        return False


def apply_rating_filter(page: Page, min_rating: float) -> bool:
    """Clicks the star-rating chip nearest min_rating, e.g. 4.3 -> "4.5+"."""
    tier = nearest_rating_tier(min_rating, config.available_rating_tiers)
    return _click_chip(page, rf"{tier}\s*\+?\s*stars?")


def apply_sort_by_sold(page: Page) -> bool:
    """Sorts the listing by units sold instead of relevance - this is what
    our filters.apply_filters() ranking assumes it's working with."""
    return _click_chip(page, CATEGORY_FILTERS["sold_sort"])


def apply_price_range(page: Page, min_price: float | None, max_price: float | None) -> bool:
    """Opens the price filter chip and fills in whichever bound(s) were
    given. No-ops (returns False) if neither bound is set."""
    if min_price is None and max_price is None:
        return False
    if not _click_chip(page, CATEGORY_FILTERS["price_chip"]):
        return False

    if min_price is not None:
        page.get_by_placeholder(re.compile("min", re.I)).fill(str(min_price))
    if max_price is not None:
        page.get_by_placeholder(re.compile("max", re.I)).fill(str(max_price))

    return _click_chip(page, CATEGORY_FILTERS["price_apply"])


def apply_shop_filters(
    page: Page,
    category: str | None = None,
    min_rating: float | None = None,
    sort_by_sold: bool = False,
    min_price: float | None = None,
    max_price: float | None = None,
) -> Page:
    """Single entry point scraper/run.py calls before harvesting. Runs in
    the order TikTok's UI expects: category first (may switch tabs), then
    the filter/sort chips that live on that page.

    Returns the active Page - always use this return value for anything
    after calling this function, since `category` may have changed which
    tab is alive.

    Every step is best-effort (logs and continues on a missing chip)
    rather than raising - a filter that didn't apply shouldn't abort an
    otherwise-working scrape.
    """
    if category:
        page = open_category(page, category)
        _human_pause()

    if min_rating is not None:
        apply_rating_filter(page, min_rating)
        _human_pause()

    if min_price is not None or max_price is not None:
        apply_price_range(page, min_price, max_price)
        _human_pause()

    if sort_by_sold:
        apply_sort_by_sold(page)
        _human_pause()

    return page