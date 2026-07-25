"""Isolates exactly what happens when you click one 'Get Link' button -
run this once and read the output, same way manual_test_baseline.py
found the real pagination/endpoint values. Answers:
  1. Does the button exist and how many are on the page?
  2. What does the item-id extraction actually return?
  3. Does clicking it fire a network request at all, and what shape?
  4. Does it open a modal instead of firing a request directly?

Usage: python3 -m scraper.shopee.manual_test_get_link (from backend/)
"""
from playwright.sync_api import sync_playwright
from seleniumbase import Driver

from scraper.session_store import load_cookies
from scraper.shopee.auth import is_logged_in, wait_for_manual_login
from scraper.shopee.config import config

SESSION_FILE = "shopee_affiliate_session.txt"
GET_LINK_BUTTON_SELECTOR = "button.AffiliateItemCard__getlinkBtn"

EXTRACT_DEBUG_JS = """
el => {
    const ancestors = [];
    let node = el;
    for (let i = 0; i < 4 && node; i++) {
        ancestors.push({ tag: node.tagName, cls: node.className });
        node = node.parentElement;
    }
    const card = el.closest('[class*="ItemCard"]');
    const link = card ? card.querySelector('a[href*="/product/"]') : null;
    return {
        ancestors,
        cardFound: !!card,
        cardClass: card ? card.className : null,
        linkHref: link ? link.href : null,
    };
}
"""

driver = Driver(uc=True, incognito=False, headless=False)
try:
    load_cookies(driver, config.offer_page_url, SESSION_FILE)
    driver.sleep(2)

    debugger_address = driver.capabilities["goog:chromeOptions"]["debuggerAddress"]
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{debugger_address}")
        page = browser.contexts[0].pages[0]

        page.goto(config.offer_page_url)
        page.wait_for_timeout(3000)

        if not is_logged_in(page):
            wait_for_manual_login(page)
            page.goto(config.offer_page_url)
            page.wait_for_timeout(3000)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)

        buttons = page.locator(GET_LINK_BUTTON_SELECTOR)
        count = buttons.count()
        print(f"\n[i] Found {count} '{GET_LINK_BUTTON_SELECTOR}' buttons on page")

        if count == 0:
            print("[!] Selector found nothing - the button class probably changed.")
            print("[i] Dumping all buttons with 'link' in their text/class instead...\n")
            all_link_buttons = page.evaluate("""
                () => Array.from(document.querySelectorAll('button')).filter(b =>
                    (b.textContent || '').toLowerCase().includes('link') ||
                    (b.className || '').toLowerCase().includes('link')
                ).map(b => ({ cls: b.className, text: b.textContent.trim() }))
            """)
            for b in all_link_buttons:
                print(b)
            browser.close()
            raise SystemExit(0)

        first_button = buttons.first
        debug_info = first_button.evaluate(EXTRACT_DEBUG_JS)
        print("\n[i] DOM debug for first button:")
        for k, v in debug_info.items():
            print(f"    {k}: {v}")

        print("\n[i] Watching ALL network responses for 6s after clicking 'Get Link'...")
        print("[i] (also watch the browser window - does a modal/popup open?)\n")

        def handle_response(response):
            ct = response.headers.get("content-type", "")
            if "json" not in ct:
                return
            print(f"[{response.status}] {response.url}")
            try:
                body = response.json()
                print(f"    body keys: {list(body.keys()) if isinstance(body, dict) else type(body)}")
                if isinstance(body, dict) and "data" in body:
                    print(f"    data: {body['data']}")
            except Exception as e:
                print(f"    (couldn't parse json: {e})")

        page.on("response", handle_response)
        first_button.scroll_into_view_if_needed()
        first_button.click()
        page.wait_for_timeout(6000)
        page.remove_listener("response", handle_response)

        print("\n[i] Done. If nothing printed above the 'Done' line, the click")
        print("[i] didn't trigger any JSON network call - check if a modal opened")
        print("[i] in the browser window instead (screenshot it if so).")

        browser.close()
finally:
    driver.quit()