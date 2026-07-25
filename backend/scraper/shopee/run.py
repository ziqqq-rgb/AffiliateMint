"""Shopee affiliate scraper entry point - hybrid pattern like
scraper/run.py, but paginated (page 1, 2, 3...) rather than
infinite-scrolled - see pagination.py for why."""
import time

from playwright.sync_api import sync_playwright
from seleniumbase import Driver

from scraper.session_store import load_cookies, save_cookies
from scraper.shopee.auth import is_logged_in, wait_for_manual_login
from scraper.shopee.config import config
from scraper.shopee.filters import apply_filters
from scraper.shopee.intercept import parse_offer_response
from scraper.shopee.link_fetcher import fetch_link_for_item
from scraper.shopee.pagination import go_to_next_page, scroll_to_bottom


SESSION_FILE = "shopee_affiliate_session.txt"


def run_shopee_scraper(min_commission_rate: float | None = None) -> list[dict]:
    driver = Driver(uc=True, incognito=False, headless=False)
    captured_offers: list[dict] = []

    try:
        load_cookies(driver, config.offer_page_url, SESSION_FILE)
        time.sleep(2.0)

        debugger_address = driver.capabilities["goog:chromeOptions"]["debuggerAddress"]
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://{debugger_address}")
            page = browser.contexts[0].pages[0]

            def handle_response(response):
                if config.offer_list_endpoint_hint not in response.url:
                    return
                try:
                    if "json" in response.headers.get("content-type", ""):
                        captured_offers.extend(parse_offer_response(response.json()))
                except Exception:
                    pass

            page.on("response", handle_response)
            page.goto(config.offer_page_url)
            page.wait_for_timeout(2500)

            if not is_logged_in(page):
                if not wait_for_manual_login(page):
                    raise RuntimeError("Shopee login timed out - no products scraped")
                save_cookies(driver, SESSION_FILE)
                page.goto(config.offer_page_url)
                page.wait_for_timeout(2500)

            _harvest_pages(page, captured_offers)

            shortlist = apply_filters(captured_offers)
            for product in shortlist:
                product["affiliate_link"] = fetch_link_for_item(page, product["shopee_item_id"])

            browser.close()
            return shortlist
    finally:
        driver.quit()


def _harvest_pages(page, captured_offers: list[dict]) -> None:
    """Walks pages 1..max_pages, stopping early once we already have
    enough passing candidates - no point paginating through 100
    products/page when shortlist_size is 10."""
    scroll_to_bottom(page)  # reveal page 1's pagination bar before checking anything

    for page_num in range(1, config.max_pages + 1):
        print(f"  -> Harvesting page {page_num}/{config.max_pages} ({len(captured_offers)} offers so far)...")

        if _enough_candidates(captured_offers):
            print(f"  -> Enough qualifying offers found, stopping early.")
            return

        if not go_to_next_page(page) and page_num > 1:
            print(f"  -> Reached last page ({page_num}).")
            return
        page.wait_for_timeout(2000)   # let the page's XHR fire and get captured


def _enough_candidates(offers: list[dict]) -> bool:
    passing = [o for o in offers if o.get("commission_rate_pct", 0) >= config.min_commission_rate]
    return len(passing) >= config.shortlist_size