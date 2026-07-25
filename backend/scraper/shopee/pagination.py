"""Page-number navigation for the Shopee affiliate offer list.
Confirmed via scraper/shopee/manual_test_baseline.py: there is no
next-arrow control - pagination is a row of SPAN.page-item.page-page
elements with literal number text ("1", "2", "3"...). Clicking one
fires /api/v3/offer/product/list again with page_offset advanced by
page_limit (20 per page, confirmed from the real request)."""
import logging

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

PAGE_NUMBER_SELECTOR = "span.page-item.page-page"


def scroll_to_bottom(page: Page, pause_ms: int = 800) -> None:
    """Scrolls the main window to the bottom - the pagination row only
    renders once the grid above it is in view."""
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(pause_ms)


def go_to_page(page: Page, page_num: int, timeout_ms: int = 5000) -> bool:
    """Clicks the page-number span matching page_num exactly. Returns
    False if that number isn't visible (fewer pages exist, or it's
    beyond what's rendered without further pagination) - callers treat
    that as "no more pages" rather than an error."""
    scroll_to_bottom(page)

    target = page.locator(PAGE_NUMBER_SELECTOR, has_text=str(page_num)).first
    try:
        target.wait_for(state="visible", timeout=timeout_ms)
        target.scroll_into_view_if_needed()
        target.click()
        return True
    except PlaywrightTimeoutError:
        logger.info(f"[+] Page {page_num} control not found - assuming last page")
        return False