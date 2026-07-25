"""Logs every JSON response while browsing the Shopee affiliate offer
page, and dumps candidate pagination elements - use this once to find
the real values for config.offer_list_endpoint_hint and
pagination.NEXT_BUTTON_SELECTOR, same way TikTok's endpoint pattern
was confirmed (see scraper/manual_test_baseline.py).

Usage: python3 -m scraper.shopee.manual_test_baseline (from backend/)
"""
from playwright.sync_api import sync_playwright
from seleniumbase import Driver

from scraper.session_store import load_cookies
from scraper.shopee.auth import is_logged_in, wait_for_manual_login
from scraper.shopee.config import config

SESSION_FILE = "shopee_affiliate_session.txt"


def dump_pagination_candidates(page) -> None:
    """Prints every small clickable element whose class/aria-label
    hints at pagination - paste the real one into NEXT_BUTTON_SELECTOR
    once you spot it."""
    candidates = page.evaluate("""
        () => {
            const els = document.querySelectorAll('[class*="pag" i], [aria-label*="page" i], button');
            const results = [];
            els.forEach(el => {
                const text = (el.textContent || '').trim();
                if (text.length > 0 && text.length < 20) {
                    results.push({
                        tag: el.tagName,
                        cls: el.className,
                        aria: el.getAttribute('aria-label'),
                        text,
                    });
                }
            });
            return results.slice(0, 40);
        }
    """)
    print("\n--- Pagination candidates ---")
    for c in candidates:
        print(c)
    print("--- end candidates ---\n")


driver = Driver(uc=True, incognito=False, headless=False)
try:
    load_cookies(driver, config.offer_page_url, SESSION_FILE)
    driver.sleep(2)

    debugger_address = driver.capabilities["goog:chromeOptions"]["debuggerAddress"]
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{debugger_address}")
        page = browser.contexts[0].pages[0]

        def handle_response(response):
            ct = response.headers.get("content-type", "")
            if "json" not in ct:
                return
            print(f"[{response.status}] {response.url}")

        page.on("response", handle_response)
        page.goto(config.offer_page_url)
        page.wait_for_timeout(3000)

        if not is_logged_in(page):
            wait_for_manual_login(page)
            page.goto(config.offer_page_url)
            page.wait_for_timeout(3000)

        print(f"\n[i] Page loaded: {page.url}")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        dump_pagination_candidates(page)

        print("[i] Now manually click page '2' in the browser window.")
        print("[i] Watch this terminal for the matching JSON request URL...\n")
        page.wait_for_timeout(20000)

        browser.close()
finally:
    driver.quit()