"""
backend/scraper/session_store.py

Cookie persistence for scraper/run.py's Playwright-over-CDP scraper.

NOTE: intentionally separate from capture_session.py's SessionManager.
That class saves/loads cookies through sb_cdp.Chrome (browser.py's
StealthBrowser) - a different SeleniumBase driver flavor than the
seleniumbase.Driver(uc=True) this file targets, which run.py needs for
its `.capabilities["goog:chromeOptions"]["debuggerAddress"]` ->
Playwright connect_over_cdp bridge. The two driver types use
incompatible cookie formats, so don't mix them.
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def save_cookies(driver, filepath: str = "affiliate_session.txt") -> None:
    """Dumps Selenium's cookie list as JSON. Run once after a manual
    browse/login session so future scrapes skip needing fresh incognito."""
    cookies = driver.get_cookies()
    Path(filepath).write_text(json.dumps(cookies, indent=2))
    logger.info(f"[+] Saved {len(cookies)} cookies to {filepath}")


def load_cookies(driver, url: str, filepath: str = "affiliate_session.txt") -> bool:
    """Navigates to `url` first (Selenium requires same-origin before
    add_cookie), injects each saved cookie, then refreshes. Returns False
    instead of raising if no session file exists yet - a scrape without
    one should still run, just less reliably against risk control."""
    path = Path(filepath)
    if not path.exists():
        logger.warning(f"[!] No saved session at {filepath} - continuing without one")
        driver.get(url)
        return False

    driver.get(url)
    cookies = json.loads(path.read_text())

    for cookie in cookies:
        cookie.pop("sameSite", None)  # Selenium rejects some sameSite values as-is
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            logger.warning(f"[!] Skipped one cookie ({cookie.get('name')}): {e}")

    driver.refresh()
    logger.info(f"[+] Loaded {len(cookies)} cookies from {filepath}")
    return True