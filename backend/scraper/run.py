"""
backend/scraper/run.py
ADVANCED HYBRID AFFILIATE INTELLIGENCE ENGINE
Extracts 14+ deep affiliate metrics per product (Sales Volume, Discounts, Ratings, Shop Data)

Two harvesting strategies run side by side and both feed the same
ProductCollector so dedup logic lives in exactly one place:
- scraper/wiretap.py   - parses every JSON network response for product data
- scraper/dom_scraper.py - reads whatever product cards are on screen right now
"""
import json
import os
import time

from playwright.sync_api import sync_playwright
from seleniumbase import Driver

from scraper.captcha import is_captcha_visible
from scraper.dom_scraper import scrape_visible_dom_products
from scraper.navigation import apply_shop_filters
from scraper.session_store import load_cookies
from scraper.wiretap import find_products

# Response URLs are matched against this list before we bother parsing
# their JSON body - keeps the wiretap from wasting time on analytics/
# tracking calls that will never contain product data.
WIRETAP_URL_KEYWORDS = (
    "/oec/", "showcase", "goods", "commodity", "search",
    "card_list", "product", "homepage_deskt", "/api/",
)

MIN_TITLE_LENGTH = 3
SCROLL_PASSES = 5
SCROLL_PIXELS = 1800


class ProductCollector:
    """Dedupes and collects harvested items as they stream in from
    either the wiretap or the DOM scraper - both call add(), so the
    "have we already seen this one" logic lives in one place."""

    def __init__(self):
        self.items: list[dict] = []
        self._seen_keys: set[str] = set()

    def add(self, item_data: dict, source: str) -> None:
        unique_key = item_data.get("product_id") or item_data.get("title")
        title = str(item_data.get("title", "")).strip()
        if not unique_key or unique_key in self._seen_keys or len(title) < MIN_TITLE_LENGTH:
            return

        self._seen_keys.add(unique_key)
        item_data["source"] = source
        self.items.append(item_data)
        self._log_captured(item_data, source)

    def _log_captured(self, item_data: dict, source: str) -> None:
        title_short = str(item_data.get("title", ""))[:40]
        price = item_data.get("sale_price_rm", "0.00")
        sold = item_data.get("units_sold", "N/A")
        discount = item_data.get("discount_percentage", "")
        disc_str = f" ({discount} OFF)" if discount else ""
        print(f"  [{source} #{len(self.items)}] -> {title_short}... | RM {price}{disc_str} | Sold: {sold}")


def run_hybrid_scraper(
    target_url,
    category=None,
    min_rating=None,
    sort_by_sold=False,
    min_price=None,
    max_price=None,
):
    print("--- Starting Advanced Hybrid Affiliate Scraper ---")
    print("[+] Launching SeleniumBase UC Mode to bypass anti-bot defenses...")
    driver = Driver(uc=True, incognito=False, headless=False)
    collector = ProductCollector()

    try:
        print(f"[+] Loading session + navigating to target -> {target_url}")
        load_cookies(driver, target_url, "affiliate_session.txt")
        time.sleep(3.5)
        _wait_out_captcha_if_visible(driver)

        debugger_address = driver.capabilities["goog:chromeOptions"]["debuggerAddress"]
        print(f"[+] Connecting Playwright to CDP Endpoint: http://{debugger_address}")

        with sync_playwright() as p:
            pw_browser = p.chromium.connect_over_cdp(f"http://{debugger_address}")
            page = pw_browser.contexts[0].pages[0]

            page.on("response", lambda response: _handle_wiretap_response(response, collector))
            print("[+] Deep JSON Wiretap Extractor ACTIVE!")

            page = apply_shop_filters(
                page,
                category=category,
                min_rating=min_rating,
                sort_by_sold=sort_by_sold,
                min_price=min_price,
                max_price=max_price,
            )
            print("[+] Deep JSON Wiretap Extractor ACTIVE!")

            _harvest_visible_dom(page, collector)
            _click_view_more(page)
            _scroll_and_harvest(page, collector)

            pw_browser.close()

    except Exception as e:
        print(f"\n[ERROR] Hybrid execution failed: {e}")

    finally:
        print("\n[+] Closing SeleniumBase defense browser...")
        driver.quit()
        _save_harvest_to_file(collector.items)

    return collector.items


def _wait_out_captcha_if_visible(driver) -> None:
    print("[+] Checking for active visible CAPTCHA...")
    if is_captcha_visible(driver):
        print("  [!] Active CAPTCHA detected on screen! Waiting 15s for manual solve...")
        time.sleep(15)
    else:
        print("  [SUCCESS] No active CAPTCHA blocking screen!")


def _handle_wiretap_response(response, collector: ProductCollector) -> None:
    url = response.url.lower()
    if not any(keyword in url for keyword in WIRETAP_URL_KEYWORDS):
        return
    try:
        if "json" in response.headers.get("content-type", ""):
            find_products(response.json(), on_product=lambda item: collector.add(item, source="WIRETAP"))
    except Exception:
        pass  # matched URL but non-JSON/malformed body - not every match is a real product feed


def _harvest_visible_dom(page, collector: ProductCollector) -> None:
    print("[+] Harvesting initial screen products...")
    for item in scrape_visible_dom_products(page):
        collector.add(item, source="DOM")


def _click_view_more(page) -> None:
    print("[+] Attempting to click 'View More' button...")
    try:
        view_more = page.locator("text=/View more/i").first
        if view_more.is_visible():
            view_more.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)
            view_more.click(force=True)
            print("[SUCCESS] Clicked 'View More' button!")
            page.wait_for_timeout(2500)
        else:
            print("[!] 'View More' button not visible directly. Triggering scroll...")
    except Exception as e:
        print(f"[!] Could not click 'View More': {e}")


def _scroll_and_harvest(page, collector: ProductCollector, passes: int = SCROLL_PASSES) -> None:
    print("[+] Starting smooth mouse-wheel infinite scroll sequence...")
    for pass_num in range(1, passes + 1):
        print(f"  -> Scroll pass {pass_num}/{passes}...")
        page.mouse.wheel(0, SCROLL_PIXELS)
        page.wait_for_timeout(2000)
        for item in scrape_visible_dom_products(page):
            collector.add(item, source="DOM")


def _save_harvest_to_file(items: list[dict], output_file: str = "tiktok_harvest.json") -> None:
    print("\n--- Final Scrape Summary ---")
    if not items:
        print("[!] No products harvested.")
        print("--- Scrape Complete ---")
        return

    print(f"[SUCCESS] Total rich products extracted: {len(items)}")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"[SUCCESS] Saved deep catalog to {os.path.abspath(output_file)}!")
    print("--- Scrape Complete ---")


if __name__ == "__main__":
    run_hybrid_scraper("https://shop.tiktok.com/my")
