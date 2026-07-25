"""Login-state detection for the Shopee affiliate dashboard. Kept
separate from run.py so the "is this actually logged in" check has one
home - the offer page silently redirects to a login form instead of
erroring, so this can't be skipped."""
import logging
import time

from playwright.sync_api import Page

logger = logging.getLogger(__name__)

LOGIN_URL_HINT = "accounts.shopee.com.my"  # Shopee's login/redirect domain


def is_logged_in(page: Page) -> bool:
    """True once the page has actually landed on the offer dashboard,
    not a login/verification screen."""
    if LOGIN_URL_HINT in page.url:
        return False
    # Dashboard renders the "Product Offer" heading once authenticated -
    # cheap DOM check beats guessing off URL alone (Shopee sometimes
    # keeps the same URL while still showing a login modal on top).
    return page.locator("text=Product Offer").first.is_visible(timeout=2000) if page.url else False


def wait_for_manual_login(page: Page, timeout_seconds: int = 120, poll_seconds: float = 2.0) -> bool:
    """Blocks until is_logged_in() is True or timeout_seconds elapses.
    Call this right after page.goto() whenever the session file might be
    stale - cheaper than always forcing a fresh manual login."""
    logger.info(f"[!] Not logged in - waiting up to {timeout_seconds}s for manual login...")
    print(f"\n[!] Please log into Shopee Affiliate in the opened browser window.")
    print(f"[!] Waiting up to {timeout_seconds}s...\n")

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            if is_logged_in(page):
                logger.info("[+] Login detected, continuing...")
                return True
        except Exception:
            pass  # page mid-navigation - just retry
        time.sleep(poll_seconds)

    return False