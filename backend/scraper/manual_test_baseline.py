"""Logs every JSON response during an 8s idle window on the homepage,
using saved session cookies - tests whether that resolves code=100000.

Usage: python3 -m scraper.manual_test_baseline (from backend/)
"""
from seleniumbase import Driver
from playwright.sync_api import sync_playwright

from scraper.session_store import load_cookies
from scraper.navigation import get_active_page

target_url = "https://shop.tiktok.com/my"
driver = Driver(uc=True, incognito=False, headless=False)

try:
    load_cookies(driver, target_url, "affiliate_session.txt")
    driver.sleep(3)

    debugger_address = driver.capabilities["goog:chromeOptions"]["debuggerAddress"]
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{debugger_address}")
        page = get_active_page(browser)
        print(f"[i] Active page URL: {page.url}\n")

        def handle_response(response):
            ct = response.headers.get("content-type", "")
            if "json" not in ct:
                return
            is_target = "homepage_desktop/products_by_component" in response.url
            marker = ">>> TARGET ENDPOINT <<<" if is_target else ""
            try:
                data = response.json()
                print(f"[{response.status}] code={data.get('code')} message={data.get('message')} {marker}")
                print(f"    url: {response.url}\n")
            except Exception:
                print(f"[{response.status}] (non-JSON body) {marker}")
                print(f"    url: {response.url}\n")

        page.on("response", handle_response)
        page.wait_for_timeout(8000)
        browser.close()
finally:
    driver.quit()