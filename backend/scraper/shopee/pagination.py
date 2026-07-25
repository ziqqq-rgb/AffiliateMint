"""Page-number navigation for the Shopee affiliate offer list. This
dashboard paginates (1,2,3,4,5...) instead of infinite-scrolling like
TikTok's storefront - the controls sit at the bottom of a long product
grid, so they must be scrolled into view before Playwright can see or
click them (a plain .click() on an off-screen element times out)."""
import logging

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

NEXT_BUTTON_SELECTOR = 'button[aria-label="next page"], .ant-pagination-next, [class*="pagination"] [class*="next"]'


def scroll_to_bottom(page: Page, pause_ms: int = 800) -> None:
    """Scrolls the main window to the bottom of the page - the product
    grid + pagination bar only render/settle once they're in view."""
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(pause_ms)


def go_to_next_page(page: Page, timeout_ms: int = 5000) -> bool:
    """Scrolls down, then clicks the '>' pagination control. Returns
    False once it's disabled/gone (last page reached) instead of
    raising - a scraper that stops at the last page is expected
    behavior, not an error."""
    scroll_to_bottom(page)

    next_button = page.locator(NEXT_BUTTON_SELECTOR).first
    try:
        next_button.wait_for(state="visible", timeout=timeout_ms)
        next_button.scroll_into_view_if_needed()
        if next_button.is_disabled():
            return False
        next_button.click()
        return True
    except PlaywrightTimeoutError:
        logger.info("[+] No next-page control found - assuming last page")
        return False